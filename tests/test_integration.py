"""Config flow, setup, sensors and reauth, end to end against the fake cloud."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.renpho_cloud.const import DOMAIN

from .conftest import EMAIL, PASSWORD, USER_ID

CREDENTIALS = {CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD}
RECORD = {
    "timeStamp": 1_700_000_000,
    "weight": "81.5",
    "bodyfat": 19.2,
    "bmr": 1750,
    "heartRate": 0,
}


async def _add_entry(hass, password=PASSWORD) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USER_ID,
        title=EMAIL,
        data={CONF_EMAIL: EMAIL, CONF_PASSWORD: password},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_user_flow_creates_entry_and_sensors(hass, cloud):
    cloud.records = [RECORD]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: EMAIL, CONF_PASSWORD: "wrong"}
    )
    assert result["errors"] == {"base": "invalid_auth"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CREDENTIALS
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == USER_ID
    await hass.async_block_till_done()

    states = {
        s.entity_id.removeprefix("sensor.me_example_com_"): s.state
        for s in hass.states.async_all("sensor")
    }
    assert states == {
        "weight": "81.5",
        "bmi": "unknown",
        "body_fat": "19.2",
        "body_water": "unknown",
        "muscle": "unknown",
        "bone": "unknown",
        "protein": "unknown",
        "subcutaneous_fat": "unknown",
        "visceral_fat": "unknown",
        "basal_metabolic_rate": "1750.0",
        "body_age": "unknown",
        "lean_body_mass": "unknown",
        "fat_free_weight": "unknown",
        "last_measurement": "2023-11-14T22:13:20+00:00",
    }


async def test_same_account_cannot_be_added_twice(hass, cloud):
    await _add_entry(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CREDENTIALS
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_changed_password_triggers_reauth_and_recovers(hass, cloud):
    entry = await _add_entry(hass, password="stale")
    assert entry.state is ConfigEntryState.SETUP_ERROR
    [flow] = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert flow["context"]["source"] == "reauth"

    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], CREDENTIALS
    )
    assert result["reason"] == "reauth_successful"
    await hass.async_block_till_done()
    assert entry.data[CONF_PASSWORD] == PASSWORD
    assert entry.state is ConfigEntryState.LOADED


async def test_unload(hass, cloud):
    entry = await _add_entry(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED
