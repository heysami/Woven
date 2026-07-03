"""editor/kinds - single source of truth for workflow node contracts.

The Python registry is authoritative; serve.py exposes a JSON export at
GET /__kinds/registry for the frontend, the validator, the reconciler,
and orchestrator skills to consume.

This package contains:
  registry.py       - KINDS dict - the contract
  validate.py       - synchronous reject checks for save / commit / status
  reconcile.py      - drift detection + auto-heal across workflow.json vs disk

Plus two docs in this directory:
  README.md         - human-readable companion to registry.py
  AGENT_HARNESS.md  - rulebook the orchestrator agent reads every turn
"""

from .registry import KINDS, kind_contract

__all__ = ["KINDS", "kind_contract"]
