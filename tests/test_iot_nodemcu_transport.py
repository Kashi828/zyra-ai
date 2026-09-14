from unittest.mock import MagicMock, patch

from core.iot_nodemcu_transport import NodeMCUTransport


def test_transport_posts_allowlisted_status_with_secret():
    response = MagicMock()
    response.status = 200
    response.read.return_value = b'{"ok":true,"device_id":"esp-01"}'
    response.__enter__.return_value = response

    with patch("core.iot_nodemcu_transport.urllib.request.urlopen", return_value=response) as urlopen:
        result = NodeMCUTransport("https://nodemcu.example", secret="test-secret").request("status")

    assert result.ok is True
    assert result.status_code == 200
    assert result.payload["device_id"] == "esp-01"
    request = urlopen.call_args.args[0]
    assert request.full_url == "https://nodemcu.example/v1/status"
    assert request.get_method() == "POST"
    assert request.get_header("X-zyra-device-secret") == "test-secret"
    assert request.data == b"{}"


def test_transport_normalizes_gpio_write_boolean_value():
    response = MagicMock()
    response.status = 200
    response.read.return_value = b'{"ok":true,"value":1}'
    response.__enter__.return_value = response

    with patch("core.iot_nodemcu_transport.urllib.request.urlopen", return_value=response) as urlopen:
        result = NodeMCUTransport("https://nodemcu.example", secret="s").request(
            "gpio.write", {"pin": 5, "value": True}
        )

    assert result.ok is True
    assert urlopen.call_args.args[0].data == b'{"pin": 5, "value": 1}'


def test_transport_rejects_invalid_endpoint_without_network_call():
    with patch("core.iot_nodemcu_transport.urllib.request.urlopen") as urlopen:
        try:
            NodeMCUTransport("http://192.168.1.50")
        except ValueError as exc:
            assert "TLS" in str(exc)
        else:
            raise AssertionError("expected TLS validation failure")
    urlopen.assert_not_called()


def test_transport_rejects_non_allowlisted_action():
    with patch("core.iot_nodemcu_transport.urllib.request.urlopen") as urlopen:
        result = NodeMCUTransport("https://nodemcu.example", secret="s").request("shell", {"cmd": "whoami"})

    assert result.ok is False
    assert result.status_code == 403
    assert result.error == "action is not allowed"
    urlopen.assert_not_called()


def test_transport_requires_gpio_write_arguments():
    with patch("core.iot_nodemcu_transport.urllib.request.urlopen") as urlopen:
        result = NodeMCUTransport("https://nodemcu.example", secret="s").request("gpio.write", {"pin": 5})

    assert result.ok is False
    assert result.status_code == 400
    assert result.error == "pin and value are required"
    urlopen.assert_not_called()
