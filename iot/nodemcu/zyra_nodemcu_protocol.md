# ZYRA NodeMCU Agent Protocol

## Purpose

A small, deterministic protocol for ESP8266/ESP32/NodeMCU devices to expose explicitly approved IoT operations to ZYRA.

## Transport

- HTTP or HTTPS on the device LAN.
- HTTPS is required when traffic leaves the loopback interface or crosses an untrusted network.
- The device must be enrolled before ZYRA treats it as an ecosystem member.
- The device secret is a shared authentication credential and must never be sent to the language model.
- Production deployments should bind the endpoint to the persistent enrolled device record; the endpoint must not be selected by an LLM-generated task.

## Firmware dependency

The reference Arduino firmware uses **ArduinoJson v7**. Install it from the Arduino Library Manager before compiling. The parser is bounded by a 192-byte request-body limit and rejects malformed JSON and unknown fields.

## Endpoints

`POST /v1/status`

Returns device identity, firmware version, uptime, and health information.

`POST /v1/gpio.read`

Request: `{ "pin": <integer> }`

Returns the current digital GPIO value for an allowlisted pin.

`POST /v1/gpio.write`

Request: `{ "pin": <integer>, "value": 0|1 }`

Writes a digital value only to an allowlisted output pin.

## Authentication

Requests from ZYRA include the enrolled device authentication header. Firmware compares credentials without early-exit comparison and rejects missing or invalid credentials with HTTP 401.

## Safety

The firmware must not implement a general command, shell, eval, arbitrary script, or arbitrary-code endpoint. GPIO pins are explicitly allowlisted in firmware configuration. Unknown JSON fields are rejected. Destructive or hardware-sensitive operations must be represented as separate capabilities and require ZYRA confirmation.

## Example status response

```json
{
  "ok": true,
  "device_id": "esp-01",
  "device_type": "nodemcu",
  "firmware": "zyra-nodemcu-1",
  "uptime_seconds": 1234
}
```

## Example GPIO write response

```json
{
  "ok": true,
  "device_id": "esp-01",
  "pin": 5,
  "value": 1
}
```
