/*
 * ZYRA AI NodeMCU reference agent
 *
 * Target: ESP8266/ESP32 Arduino environments.
 * Exposes only status and digital GPIO operations.
 * Replace placeholders before flashing a real device.
 */

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char* WIFI_SSID = "CHANGE_ME";
const char* WIFI_PASSWORD = "CHANGE_ME";
const char* ZYRA_DEVICE_ID = "esp-01";
const char* ZYRA_SECRET = "CHANGE_ME_LONG_RANDOM_SECRET";

ESP8266WebServer server(80);

bool authenticated() {
  if (!server.hasHeader("X-Zyra-Device-Secret")) return false;
  return server.header("X-Zyra-Device-Secret") == String(ZYRA_SECRET);
}

bool validPin(int pin) {
  // Explicitly allow only the pins selected for this device.
  return pin == D1 || pin == D2;
}

void requireAuth() {
  if (!authenticated()) {
    server.send(401, "application/json", "{\"ok\":false,\"error\":\"unauthorized\"}");
    return;
  }
}

void statusRoute() {
  if (!authenticated()) {
    server.send(401, "application/json", "{\"ok\":false,\"error\":\"unauthorized\"}");
    return;
  }
  String body = String("{\"ok\":true,\"device_id\":\"") + ZYRA_DEVICE_ID +
                "\",\"device_type\":\"nodemcu\",\"uptime_seconds\":" +
                String(millis() / 1000) + "}";
  server.send(200, "application/json", body);
}

void gpioReadRoute() {
  if (!authenticated()) {
    server.send(401, "application/json", "{\"ok\":false,\"error\":\"unauthorized\"}");
    return;
  }
  if (!server.hasArg("plain")) {
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"body_required\"}");
    return;
  }
  // Reference firmware intentionally keeps JSON parsing minimal.
  // Production firmware should use a bounded JSON parser and reject unknown fields.
  server.send(400, "application/json", "{\"ok\":false,\"error\":\"use_bounded_json_parser\"}");
}

void gpioWriteRoute() {
  if (!authenticated()) {
    server.send(401, "application/json", "{\"ok\":false,\"error\":\"unauthorized\"}");
    return;
  }
  // GPIO writes require a bounded JSON parser in the device implementation.
  // This reference endpoint is deliberately fail-closed until that parser is added.
  server.send(501, "application/json", "{\"ok\":false,\"error\":\"reference_firmware_requires_parser\"}");
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
