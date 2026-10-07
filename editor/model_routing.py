"""Model IDs are data. Runtime selection and execution policy are separate.

Legacy IDs remain accepted. Prefix an opaque ID with a runtime (for example
opencode:google/gemini-custom), or register a named model in modelCatalog.
Only migration defaults name particular models; execution never branches on ID.
"""
import copy
import re

RUNTIMES = ("claude", "codex", "opencode")
DEFAULTS = {"claude": "claude-haiku-4-5", "codex": "gpt-5.6-luna",
            "opencode": "opencode-default"}
PROVIDERS = {"claude": "anthropic", "codex": "openai", "opencode": "opencode"}
BUILTIN_CAPABILITIES = {"claude-haiku-4-5": {"efforts": []},
                        "gpt-5.6-luna": {"efforts": ["low", "medium", "high", "xhigh", "max"]}}


def valid_model(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./:@+-]{0,199}", value))


def validate_catalog(rows):
    if not isinstance(rows, list) or len(rows) > 500:
        raise ValueError("modelCatalog must be a list of at most 500 models")
    out, seen = [], set()
    for row in rows:
        if not isinstance(row, dict) or not valid_model(row.get("id")) or row["id"] in seen:
            raise ValueError("registered models need unique valid IDs")
        if row.get("runtime") not in RUNTIMES or not valid_model(row.get("model")):
            raise ValueError("registered models need a runtime and exact model ID")
        seen.add(row["id"])
        item = {k: copy.deepcopy(row[k]) for k in ("id", "model", "runtime", "label", "modalities", "efforts") if k in row}
        for key in ("modalities", "efforts"):
            if key in item and (not isinstance(item[key], list) or not all(isinstance(v, str) for v in item[key])):
                raise ValueError(key + " must be a list of strings")
        if "label" in item and not isinstance(item["label"], str):
            raise ValueError("model label must be text")
        out.append(item)
    return out


def validate_economy(value):
    if not isinstance(value, dict) or any(k not in RUNTIMES or not valid_model(v) for k, v in value.items()):
        raise ValueError("economyModels must map runtimes to exact model IDs or registered models")
    return dict(value)


def resolve(setting=None, runtime="claude", inherited=None, config=None, role="agent"):
    """Return a serializable execution snapshot, never silently switch runtime.

    Explicit registered or runtime-qualified choices may switch runtime. Legacy
    provider IDs route helpers across runtimes for compatibility. Inherit always
    pins the parent's runtime, including its deliberate CLI-default selection.
    """
    if runtime not in RUNTIMES:
        raise ValueError("unknown runtime: " + str(runtime))
    config = config or {}
    requested = setting or "inherit"
    inherited_choice = requested == "inherit"
    if requested == "fast":
        setting = {**DEFAULTS, **config.get("economyModels", {})}[runtime]
    elif inherited_choice:
        setting = inherited or runtime + "-default"
    if not valid_model(setting):
        raise ValueError("invalid model selection")
    # inherited is the parent's frozen native ID, not a fresh catalog lookup.
    row = None if inherited_choice else next((r for r in config.get("modelCatalog", []) if r["id"] == setting), None)
    if row:
        runtime, model = row["runtime"], row["model"]
    elif setting.partition(":")[0] in RUNTIMES and ":" in setting:
        runtime, model = setting.split(":", 1)
    else:
        model = setting
        if not inherited_choice and runtime != "opencode":
            if model.startswith("claude-") or model in ("opus", "sonnet", "haiku"):
                runtime = "claude"
            elif re.match(r"^(gpt-|codex-|o\d)", model):
                runtime = "codex"
    if not valid_model(model):
        raise ValueError("invalid exact model ID")
    if model.endswith("-default") and model in {r + "-default" for r in RUNTIMES}:
        if model != runtime + "-default":
            raise ValueError("CLI default belongs to a different runtime")
        model = None
    return {"version": 1, "role": role, "runtime": runtime,
            "connection": runtime + "-cli", "requestedModel": requested,
            "model": model, "resolvedModel": None,
            "isolation": "text-only" if role in ("summary", "writer") else "workspace",
            "reasoning": "low" if requested == "fast" else None,
            "capabilities": {**copy.deepcopy(BUILTIN_CAPABILITIES.get(model, {})),
                **{k: copy.deepcopy(row[k]) for k in ("modalities", "efforts") if row and k in row}}}


def spawn_model(runtime, model, config=None):
    if not model or model == runtime + "-default":
        return []
    choice = resolve(model, runtime=runtime, config=config)
    if choice["runtime"] != runtime:
        raise ValueError("model requires %s, selected runtime is %s" % (choice["runtime"], runtime))
    return ["--model", choice["model"]] if choice["model"] else []
