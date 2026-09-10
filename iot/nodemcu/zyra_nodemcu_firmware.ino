/*
 * ZYRA AI NodeMCU bounded agent firmware
 *
 * Targets ESP8266 and ESP32 Arduino environments.
 * Exposes only status and allowlisted digital GPIO operations.
 *
 * Dependency: ArduinoJson v7 (install through Arduino Library Manager).
 * Replace all configuration placeholders before flashing a real device.
 */

#include <Arduino.h>
#include <ArduinoJson.h>

#if defined(ESP8266)
  #include <ESP8266WiFi.h>
  #include <ESP8266WebServer.h>
  ESP8266WebServer server(80);
#elif defined(ESP32)
  #include <WiFi.h>
  #include <WebServer.h>
  WebServer server(80);
#else
  #error "ZYRA NodeMCU firmware requires ESP8266 or ESP32"
#endif

const char* WIFI_SSID = "CHANGE_ME";
const char* WIFI_PASSWORD = "CHANGE_ME";
const char* ZYRA_DEVICE_ID = "esp-01";
const char* ZYRA_SECRET = "CHANGE_ME_LONG_RANDOM_SECRET";

// Hard upper bound prevents oversized request bodies from consuming MCU memory.
constexpr size_t MAX_JSON_BODY = 192;

// Explicit hardware allowlist. Expand only through reviewed firmware changes.
bool validPin(int pin) {
  return pin == D1 || pin == D2;
}

bool constantTimeEquals(const String& supplied, const char* expected) {
  const size_t expectedLen = strlen(expected);
  const size_t suppliedLen = supplied.length();
  size_t diff = suppliedLen ^ expectedLen;
  const size_t n = suppliedLen > expectedLen ? suppliedLen : expectedLen;
  for (size_t i = 0; i < n; ++i) {
    const uint8_t a = i < suppliedLen ? static_cast<uint8_t>(supplied[i]) : 0;
    const uint8_t b = i < expectedLen ? static_cast<uint8_t>(expected[i]) : 0;
    diff |= static_cast<size_t>(a ^ b);
  }
  return diff == 0;
}

bool authenticated() {
  if (!server.hasHeader("X-Zyra-Device-Secret")) return false;
  return constantTimeEquals(server.header("X-Zyra-Device-Secret"), ZYRA_SECRET);
}

void sendJson(int status, JsonDocument& doc) {
  String body;
  serializeJson(doc, body);
  server.send(status, "application/json", body);
}

void sendError(int status, const char* error) {
  JsonDocument doc;
  doc["ok"] = false;
  doc["error"] = error;
  sendJson(status, doc);
}

bool requireAuth() {
  if (!authenticated()) {
    sendError(401, "unauthorized");
    return false;
  }
  return true;
}

bool readBoundedJson(JsonDocument& doc) {
  if (!server.hasArg("plain")) {
    sendError(400, "body_required");
    return false;
  }

  const String& body = server.arg("plain");
  if (body.length() == 0 || body.length() > MAX_JSON_BODY) {
    sendError(413, "body_too_large_or_empty");
    return false;
  }

  DeserializationError error = deserializeJson(doc, body);
  if (error) {
    sendError(400, "invalid_json");
    return false;
  }
  if (!doc.is<JsonObject>()) {
    sendError(400, "object_required");
    return false;
  }
  return true;
}

bool rejectUnknownFields(JsonObject obj, const char* const* allowed, size_t count) {
  for (JsonPair pair : obj) {
    bool known = false;
    for (size_t i = 0; i < count; ++i) {
      if (strcmp(pair.key().c_str(), allowed[i]) == 0) {
        known = true;
        break;
      }
    }
    if (!known) return false;
  }
  return true;
}

void statusRoute() {
  if (!requireAuth()) return;

  JsonDocument doc;
  doc["ok"] = true;
  doc["device_id"] = ZYRA_DEVICE_ID;
  doc["device_type"] = "nodemcu";
  doc["firmware"] = "zyra-nodemcu-1";
  doc["uptime_seconds"] = millis() / 1000UL;
  sendJson(200, doc);
}

void gpioReadRoute() {
  if (!requireAuth()) return;

  JsonDocument doc;
  if (!readBoundedJson(doc)) return;
  JsonObject obj = doc.as<JsonObject>();
  const char* const allowed[] = {"pin"};
  if (!rejectUnknownFields(obj, allowed, 1)) {
    sendError(400, "unknown_field");
    return;
  }
  if (!obj["pin"].is<int>()) {
    sendError(400, "pin_integer_required");
    return;
  }

  const int pin = obj["pin"].as<int>();
  if (!validPin(pin)) {
    sendError(403, "pin_not_allowlisted");
    return;
  }

  pinMode(pin, INPUT);
  JsonDocument response;
  response["ok"] = true;
  response["device_id"] = ZYRA_DEVICE_ID;
  response["pin"] = pin;
  response["value"] = digitalRead(pin) ? 1 : 0;
  sendJson(200, response);
}

void gpioWriteRoute() {
  if (!requireAuth()) return;

  JsonDocument doc;
  if (!readBoundedJson(doc)) return;
  JsonObject obj = doc.as<JsonObject>();
  const char* const allowed[] = {"pin", "value"};
  if (!rejectUnknownFields(obj, allowed, 2)) {
    sendError(400, "unknown_field");
    return;
  }
  if (!obj["pin"].is<int>() || !obj["value"].is<int>()) {
    sendError(400, "pin_and_value_integers_required");
    return;
  }

  const int pin = obj["pin"].as<int>();
  const int value = obj["value"].as<int>();
  if (!validPin(pin)) {
    sendError(403, "pin_not_allowlisted");
    return;
  }
  if (value != 0 && value != 1) {
    sendError(400, "value_must_be_0_or_1");
    return;
  }

  pinMode(pin, OUTPUT);
  digitalWrite(pin, value == 1 ? HIGH : LOW);

  JsonDocument response;
  response["ok"] = true;
  response["device_id"] = ZYRA_DEVICE_ID;
  response["pin"] = pin;
  response["value"] = value;
  sendJson(200, response);
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) delay(250);

  server.collectHeaders("X-Zyra-Device-Secret");
  server.on("/v1/status", HTTP_POST, statusRoute);
  server.on("/v1/gpio.read", HTTP_POST, gpioReadRoute);
  server.on("/v1/gpio.write", HTTP_POST, gpioWriteRoute);
  server.begin();
}

void loop() {
  server.handleClient();
}
