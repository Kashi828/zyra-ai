from core.iot_nodemcu_transport import NodeMCUTransport


def test_rejects_non_tls_remote_endpoint():
    try:
        NodeMCUTransport("http://192.168.1.50")
    except ValueError as exc:
        assert "TLS" in str(exc)
    else:
        raise AssertionError("remote HTTP endpoint was accepted")


def test_rejects_arbitrary_action():
    transport = NodeMCUTransport("http://127.0.0.1")
    result = transport.request("shell", {"command": "whoami"})
    assert result.ok is False
    assert result.status_code == 403


def test_validates_gpio_write_arguments():
    transport = NodeMCUTransport("http://127.0.0.1")
    result = transport.request("gpio.write", {"pin": "D1", "value": 1})
    assert result.ok is False
    assert result.status_code == 400
