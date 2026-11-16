"""Diagnostics download: the newest raw record, with account details removed."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .coordinator import RenphoConfigEntry

# shortcut: ids are redacted by key name; add any other identifying field seen in a record.
_REDACT = {CONF_EMAIL, CONF_PASSWORD, "token", "user_id", "userId", "id", "uid"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: RenphoConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), _REDACT),
        "last_update_success": coordinator.last_update_success,
        "latest_record": async_redact_data(coordinator.data or {}, _REDACT),
    }
