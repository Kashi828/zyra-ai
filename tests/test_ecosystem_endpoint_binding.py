from api.ecosystem_routes import _validate_endpoint


def test_private_http_endpoint_is_allowed():
    assert _validate_endpoint("http://192.168.1.50:80") == "http://192.168.1.50:80"


def test_loopback_http_endpoint_is_allowed():
    assert _validate_endpoint("http://127.0.0.1:8080/") == "http://127.0.0.1:8080"


def test_public_http_endpoint_is_rejected():
    try:
        _validate_endpoint("http://8.8.8.8:80")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
    else:
        raise AssertionError("public HTTP endpoint must be rejected")


def test_endpoint_credentials_are_rejected():
    try:
        _validate_endpoint("https://user:pass@192.168.1.50")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
    else:
        raise AssertionError("endpoint credentials must be rejected")


def test_endpoint_query_and_fragment_are_rejected():
    for endpoint in ("https://192.168.1.50/?token=x", "https://192.168.1.50/#x"):
        try:
            _validate_endpoint(endpoint)
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 400
        else:
            raise AssertionError("endpoint metadata must not carry query or fragment")
