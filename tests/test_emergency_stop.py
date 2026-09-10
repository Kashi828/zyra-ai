import pytest

from security.emergency_stop import EmergencyStop


def test_stop_fails_closed():
    stop = EmergencyStop()
    assert stop.allows()
    stop.engage("user requested stop")
    assert not stop.allows()
    with pytest.raises(PermissionError, match="emergency stop"):
        stop.require_running()


def test_release_restores_execution_gate():
    stop = EmergencyStop()
    stop.engage()
    stop.release()
    stop.require_running()
    assert stop.snapshot().stopped is False
