# ZYRA NodeMCU Agent Protocol

## Purpose

A small, deterministic protocol for ESP8266/ESP32/NodeMCU devices to expose explicitly approved IoT operations to ZYRA.

## Transport

- HTTP or HTTPS on the device LAN.
- HTTPS is required when traffic leaves the loopback interface or crosses an untrusted network.
- The device must be enrolled before ZYRA treats it as an ecosystem member.
- The device secret is a shared authentication credential and must never be sent to the language model.

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

Requests from ZYRA include the enrolled device authentication header. Firmware should compare credentials using a constant-time comparison and reject missing or invalid credentials with HTTP 401.

## Safety

The firmware must not implement a general command, shell, eval, arbitrary script, or arbitrary-code endpoint. GPIO pins should be explicitly allowlisted in firmware configuration. Destructive or hardware-sensitive operations should be represented as separate capabilities and require ZYRA confirmation.

## Example response

```json
{
  "ok": true,
  "device_id": "esp-01",
  "device_type": "nodemcu",
  "firmware": "zyra-nodemcu-1",
  "uptime_seconds": 1234
}
```
