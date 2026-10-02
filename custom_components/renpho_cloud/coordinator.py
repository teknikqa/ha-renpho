"""Polls the Renpho cloud for the latest measurement."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RenphoAuthError, RenphoClient, RenphoError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type RenphoConfigEntry = ConfigEntry[RenphoCoordinator]


class RenphoCoordinator(DataUpdateCoordinator[dict[str, Any] | None]):
    """Holds the newest raw measurement record, or None before the first weigh-in."""

    config_entry: RenphoConfigEntry

    def __init__(self, hass: HomeAssistant, entry: RenphoConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=30),
        )
        self.client = RenphoClient(
            async_get_clientsession(hass),
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
        )

    async def _async_update_data(self) -> dict[str, Any] | None:
        try:
            return await self.client.latest_measurement()
        except RenphoAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except RenphoError as err:
            raise UpdateFailed(str(err)) from err
