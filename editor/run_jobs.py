"""Replayable native job state. A launch acknowledgement is not completion."""
import copy
import re

TERMINAL = frozenset(("completed", "failed", "stopped", "killed", "cancelled"))
ACTIVE = frozenset(("pending", "running", "unknown"))

# Subagents that grade work the thread already did: the chat checks
# (capabilities.py visual / dsGuard / reqQa) and the lens judges. A user
# message that reaches the run while one is in flight cancels it (serve.py
# _cancel_qa_checks), because it is grading the state the user just steered
# away from.
QA_CHECK_AGENTS = {
    "visual-verifier": "visual verification",
    "ds-guardian": "DS guard",
    "craft-lens": "craft lens",
    "aesthetic-lens": "aesthetic lens",
    "concept-lens": "concept lens",
}


def qa_check(subagent_type, prompt=""):
    """The QA check a subagent dispatch runs, or None. Claude namespaces plugin
    agents (`woven:visual-verifier`); requirement QA is a general-purpose
    dispatch, recognisable only by the playbook its brief points at."""
    name = str(subagent_type or "").rsplit(":", 1)[-1].strip()
    if name in QA_CHECK_AGENTS:
        return QA_CHECK_AGENTS[name]
    if "requirement-qa.md" in str(prompt or ""):
        return "requirement QA"
    return None


def observe(jobs, event, runtime):
    """Compatibility events for older CLIs lacking explicit task status."""
    kind = event.get("type")
    if kind == "tool_use" and event.get("name") in ("Agent", "Task", "task", "spawn_agent"):
        if any(v.get("toolUseId") == event.get("id") for v in jobs.values()):
            return None
        inp = event.get("input") or {}
        job = {"type": "job", "jobId": event.get("id"), "toolUseId": event.get("id"),
               "source": "native", "runtime": runtime, "status": "pending",
               "background": inp.get("run_in_background", inp.get("background", False)),
               "description": inp.get("description"), "required": True}
        # Only the thread's OWN checks. A lens a subagent dispatched belongs to
        # that subagent's loop; the user's message does not reach it.
        check = None if event.get("sidechain") else qa_check(inp.get("subagent_type"), inp.get("prompt"))
        if check:
            job["qaCheck"] = check
        return job
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


# `waived` marks a job the daemon stopped on purpose (a QA check cancelled by
# the user's message). Its stop is not a worker failure, and later lifecycle
# frames re-send required=True, so the waiver is its own sticky key.
def pending(jobs):
    return [v for v in jobs.values() if v.get("required", True) and not v.get("waived")
            and v.get("status") not in TERMINAL]


def failed(jobs):
    return [v for v in jobs.values() if v.get("required", True) and not v.get("waived")
            and v.get("status") in TERMINAL - {"completed"}]


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
