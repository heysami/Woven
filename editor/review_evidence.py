"""Evidence provenance and honest separation of rendering from visual review."""


def attach(report, expected=None):
    result = dict(report)
    judge = result.get("judge") or {}
    mechanical = result.get("renderVerdict", result.get("verdict"))
    status = "not-requested" if not expected else "unavailable" if not judge.get("available") else (
        "passed" if judge.get("ok") is True else "failed" if judge.get("ok") is False else "inconclusive")
    result["visualReview"] = {"status": status, "model": judge.get("model"),
        "transport": judge.get("transport"), "expected": expected, "frames": judge.get("stripFrames")}
    result["renderVerdict"] = mechanical
    if expected and status != "passed" and mechanical == "pass":
        result["verdict"] = "effect-wrong" if status == "failed" else "inconclusive"
    return result
