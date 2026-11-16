"""Config flow for the Renpho Health integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_REAUTH,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import RenphoAuthError, RenphoClient, RenphoConnectionError, RenphoError
from .const import CONF_POLL_MINUTES, DEFAULT_POLL_MINUTES, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


class RenphoOptionsFlow(OptionsFlowWithReload):
    """How often to ask the Renpho cloud for a new weigh-in."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_POLL_MINUTES: int(user_input[CONF_POLL_MINUTES])}
            )
        current = self.config_entry.options.get(CONF_POLL_MINUTES, DEFAULT_POLL_MINUTES)
        schema = vol.Schema(
            {
                vol.Required(CONF_POLL_MINUTES, default=current): NumberSelector(
                    NumberSelectorConfig(
                        min=5,
                        max=1440,
                        step=1,
                        unit_of_measurement="min",
                        mode=NumberSelectorMode.BOX,
                    )
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


class RenphoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Sign in to a Renpho Health account. Reauth reuses the same form."""

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> RenphoOptionsFlow:
        return RenphoOptionsFlow()

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = RenphoClient(
                async_get_clientsession(self.hass),
                user_input[CONF_EMAIL],
                user_input[CONF_PASSWORD],
            )
            try:
                await client.login()
            except RenphoAuthError:
                errors["base"] = "invalid_auth"
            except RenphoConnectionError:
                errors["base"] = "cannot_connect"
            except RenphoError as err:
                # Keeps the server's code and message (e.g. -114) in the HA log.
                _LOGGER.warning("Renpho rejected the login: %s", err)
                errors["base"] = "login_rejected"
            else:
                await self.async_set_unique_id(client.user_id)
                if self.source == SOURCE_REAUTH:
                    self._abort_if_unique_id_mismatch(reason="wrong_account")
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(), data_updates=user_input
                    )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_EMAIL], data=user_input
                )
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_user()
