"""Shared helpers for tool backend selection."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

_DEFAULT_BROWSER_PROVIDER = "local"
_DEFAULT_MODAL_MODE = "auto"
_VALID_MODAL_MODES = {"auto", "direct"}


def normalize_browser_cloud_provider(value: object | None) -> str:
    """Return a normalized browser provider key."""
    provider = str(value or _DEFAULT_BROWSER_PROVIDER).strip().lower()
    return provider or _DEFAULT_BROWSER_PROVIDER


def coerce_modal_mode(value: object | None) -> str:
    """Return the requested modal mode when valid, else the default."""
    mode = str(value or _DEFAULT_MODAL_MODE).strip().lower()
    if mode in _VALID_MODAL_MODES:
        return mode
    return _DEFAULT_MODAL_MODE


def normalize_modal_mode(value: object | None) -> str:
    """Return a normalized modal execution mode."""
    return coerce_modal_mode(value)


def has_direct_modal_credentials() -> bool:
    """Return True when direct Modal credentials/config are available."""
    return bool(
        (os.getenv("MODAL_TOKEN_ID") and os.getenv("MODAL_TOKEN_SECRET"))
        or (Path.home() / ".modal.toml").exists()
    )


def resolve_modal_backend_state(
    modal_mode: object | None,
    *,
    has_direct: bool,
) -> Dict[str, Any]:
    """Resolve direct Modal backend selection.

    Semantics:
    - ``direct`` means direct-only
    - ``auto`` uses direct if available
    """
    requested_mode = coerce_modal_mode(modal_mode)
    normalized_mode = normalize_modal_mode(modal_mode)

    if normalized_mode == "direct":
        selected_backend = "direct" if has_direct else None
    else:
        selected_backend = "direct" if has_direct else None

    return {
        "requested_mode": requested_mode,
        "mode": normalized_mode,
        "has_direct": has_direct,
        "selected_backend": selected_backend,
    }
