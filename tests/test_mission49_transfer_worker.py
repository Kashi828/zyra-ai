from communication.transfer_worker import TransferRecoveryWorker

class Decision:
    def __init__(self, transfer_id, action, resume_bytes):
        self.transfer_id = transfer_id
        self.action = action
        self.resume_bytes = resume_bytes

class Recovery:
    def scan(self):
        return [
            Decision("t1", "resume", 40),
            Decision("t2", "resume_from_disk", 20),
            Decision("t3", "restart", 0),
            Decision("t4", "fail", 0),
        ]

def test_run_once_dispatches_only_resume_jobs():
    seen = []
    worker = TransferRecoveryWorker(Recovery(), seen.append)
    jobs = worker.run_once()
    assert [(j.transfer_id, j.resume_bytes) for j in jobs] == [("t1", 40), ("t2", 20)]
    assert seen == jobs

def test_invalid_interval_rejected():
    try:
        TransferRecoveryWorker(Recovery(), lambda _: None, interval_seconds=0)
    except ValueError:
        pass
    else:
        assert False

def test_start_stop_are_idempotent():
    worker = TransferRecoveryWorker(Recovery(), lambda _: None, interval_seconds=60)
    worker.start()
    worker.start()
    worker.stop()
    worker.stop()
