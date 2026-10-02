"""Renpho Health: body composition from the Renpho cloud."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import RenphoConfigEntry, RenphoCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: RenphoConfigEntry) -> bool:
    """Set up one Renpho account."""
    coordinator = RenphoCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RenphoConfigEntry) -> bool:
    """Unload one Renpho account."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
