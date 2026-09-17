"""Replayable native job state. A launch acknowledgement is not completion."""
import copy
import re

TERMINAL = frozenset(("completed", "failed", "stopped", "killed", "cancelled"))
ACTIVE = frozenset(("pending", "running", "unknown"))


def observe(jobs, event, runtime):
    """Compatibility events for older CLIs lacking explicit task status."""
    kind = event.get("type")
    if kind == "tool_use" and event.get("name") in ("Agent", "Task", "task", "spawn_agent"):
        if any(v.get("toolUseId") == event.get("id") for v in jobs.values()):
            return None
        inp = event.get("input") or {}
        return {"type": "job", "jobId": event.get("id"), "toolUseId": event.get("id"),
                "source": "native", "runtime": runtime, "status": "pending",
                "background": inp.get("run_in_background", inp.get("background", False)),
                "description": inp.get("description"), "required": True}
    if kind == "tool_result":
        prev = next((v for v in jobs.values() if v.get("toolUseId") == event.get("toolUseId")), None)
        if not prev or prev.get("status") in TERMINAL:
            return None
        # Explicit background jobs are owned by lifecycle notifications.
        # A synchronous Claude result can include agentId in its answer too.
        native_status = prev.get("jobId") != prev.get("toolUseId")
        launched = re.search(r"(?i)(launched|running in (?:the )?background|background task|task_id.*running)", str(event.get("content") or ""))
        waiting = prev.get("background") or launched or (native_status and prev.get("background") is not False)
        status = "failed" if event.get("isError") else "running" if waiting else "completed"
        return {**prev, "type": "job", "status": status}
    return None


def reduce_job(jobs, event):
    if event.get("type") != "job":
        return
    identity = event.get("jobId") or event.get("taskId") or event.get("toolUseId")
    if not identity:
        return
    # A launch can be seen before the task ID. Merge on the parent tool ID.
    old_key = next((k for k, v in jobs.items() if event.get("toolUseId")
                    and k == event["toolUseId"] and v.get("toolUseId") == event["toolUseId"]), identity)
    alias = jobs.pop(old_key, {}) if old_key != identity else {}
    prev = {**alias, **jobs.get(identity, {})}
    # A native turn start can reopen an existing child session. A delayed
    # completion from an older turn cannot complete the new work.
    different_attempt = event.get("attemptId") and prev.get("attemptId") and event["attemptId"] != prev["attemptId"]
    if different_attempt and not event.get("restart"):
        return
    value = {**prev, **{k: copy.deepcopy(v) for k, v in event.items() if v is not None}}
    # Replayed progress must not resurrect a completed job.
    if prev.get("status") in TERMINAL and event.get("status") not in TERMINAL and not event.get("restart"):
        value["status"] = prev["status"]
    if prev.get("status") == "completed" and event.get("resourceClosed"):
        value["status"] = "completed"
    value["restart"] = bool(event.get("restart"))
    value.setdefault("status", "running")
    value.setdefault("required", True)
    jobs[identity] = value


def pending(jobs):
    return [v for v in jobs.values() if v.get("required", True) and v.get("status") not in TERMINAL]


def failed(jobs):
    return [v for v in jobs.values() if v.get("required", True) and v.get("status") in TERMINAL - {"completed"}]


def claude_job(frame):
    sub = frame.get("subtype")
    if sub not in ("task_started", "task_updated", "task_notification", "task_progress"):
        return None
    patch = frame.get("patch") or {}
    status = patch.get("status") or frame.get("status")
    if not status and sub in ("task_started", "task_progress"):
        status = "running"
    return {"type": "job", "source": "native", "runtime": "claude",
            "jobId": frame.get("task_id"), "toolUseId": frame.get("tool_use_id"),
            "status": status, "background": patch.get("is_backgrounded"),
            "description": frame.get("description") or frame.get("summary"),
            "outputFile": frame.get("output_file"), "usage": frame.get("usage"),
            "taskType": frame.get("task_type"), "required": True}
