"""Bounded, cancellable helper executions shared by summaries and writers."""
import contextlib
import os
import signal
import subprocess
import threading

_LOCAL = threading.local()
_LOCK = threading.Lock()
_JOBS = {}
_SLOTS = threading.Condition()
_ACTIVE = {}


class Cancelled(RuntimeError):
    pass


def _cancelled(job):
    return job["cancel"].is_set() or (job.get("cancelled") and job["cancelled"]())


@contextlib.contextmanager
def execution(job_id, parent, runtime, limit=2, cancelled=None):
    previous = getattr(_LOCAL, "job", None)
    job = {"id": job_id, "parent": parent, "cancel": threading.Event(), "proc": None, "cancelled": cancelled}
    with _LOCK:
        _JOBS[job_id] = job
    acquired = False
    try:
        while not acquired:
            if _cancelled(job):
                raise Cancelled("helper cancelled while queued")
            with _SLOTS:
                if _ACTIVE.get(runtime, 0) < limit:
                    _ACTIVE[runtime] = _ACTIVE.get(runtime, 0) + 1
                    acquired = True
                else:
                    _SLOTS.wait(.1)
        _LOCAL.job = job
        yield
    finally:
        _LOCAL.job = previous
        if acquired:
            with _SLOTS:
                _ACTIVE[runtime] -= 1
                _SLOTS.notify_all()
        with _LOCK:
            _JOBS.pop(job_id, None)


def _signal(proc, sig):
    if proc and proc.poll() is None:
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            pass


def cancel(parent):
    with _LOCK:
        jobs = [j for j in _JOBS.values() if j["parent"] == parent]
    for job in jobs:
        job["cancel"].set()
        _signal(job["proc"], signal.SIGTERM)
        def reap(proc):
            if proc:
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    _signal(proc, signal.SIGKILL)
        threading.Thread(target=reap, args=(job["proc"],), daemon=True).start()


def run(args, capture_output=True, text=True, timeout=None, **kwargs):
    job = getattr(_LOCAL, "job", None)
    if job is None:
        return subprocess.run(args, capture_output=capture_output, text=text, timeout=timeout, **kwargs)
    # Register the process atomically with cancellation. Otherwise a stop
    # between Popen and assignment could miss the process's escalation timer.
    with _LOCK:
        if _cancelled(job):
            raise Cancelled("helper cancelled")
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=text, start_new_session=True, **kwargs)
        job["proc"] = proc
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _signal(proc, signal.SIGKILL)
        proc.communicate()
        raise
    if _cancelled(job):
        raise Cancelled("helper cancelled")
    return subprocess.CompletedProcess(args, proc.returncode, stdout, stderr)
