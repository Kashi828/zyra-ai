from desktop.backend_supervisor import BackendConfig, BackendSupervisor, BackendSupervisorError


class FakeSocket:
    def close(self): pass


class FakeProcess:
    def __init__(self, alive=True):
        self.alive=alive
        self.terminated=False
    def poll(self):
        return None if self.alive else 1
    def terminate(self):
        self.terminated=True
        self.alive=False
    def wait(self, timeout=None):
        return 0
    def kill(self):
        self.alive=False


def test_supervisor_builds_loopback_command():
    s=BackendSupervisor(BackendConfig(port=8123))
    assert s.command()[-1] == "8123"
    assert "--host" in s.command()
    assert "127.0.0.1" in s.command()


def test_supervisor_health_uses_socket():
    calls=[]
    def sock(addr,timeout=None):
        calls.append((addr,timeout))
        return FakeSocket()
    s=BackendSupervisor(socket_factory=sock)
    assert s.is_healthy()
    assert calls[0][0] == ("127.0.0.1",8000)


def test_supervisor_start_waits_until_healthy():
    processes=[]
    checks=[False,True]
    def popen(*args,**kwargs):
        p=FakeProcess()
        processes.append(p)
        return p
    def sock(addr,timeout=None):
        if checks:
            healthy=checks.pop(0)
        else:
            healthy=True
        if healthy: return FakeSocket()
        raise OSError("not ready")
    s=BackendSupervisor(
        BackendConfig(startup_timeout=1,poll_interval=0.001),
        popen_factory=popen, socket_factory=sock
    )
    s.start()
    assert len(processes)==1


def test_supervisor_restart_limit():
    s=BackendSupervisor(BackendConfig(max_restarts=1))
    s.process=FakeProcess()
    s.stop=lambda: None
    s.start=lambda: None
    s.restart()
    assert s.restarts == 1
    try:
        s.restart()
    except BackendSupervisorError as e:
        assert "restart limit" in str(e)
    else:
        assert False


def test_supervisor_stop_terminates_process():
    p=FakeProcess()
    s=BackendSupervisor()
    s.process=p
    s.stop()
    assert p.terminated
    assert s.process is None
