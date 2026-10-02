"""The API client against the fake cloud."""

from __future__ import annotations

import aiohttp
import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMockResponse as Response,
)

from custom_components.renpho_cloud.api import (
    BASE_URL,
    DEVICES,
    LOGIN,
    MEASUREMENTS,
    RenphoAuthError,
    RenphoClient,
    RenphoConnectionError,
    decrypt_bytes,
    encrypt,
    timestamp,
)

from .conftest import EMAIL, PASSWORD, USER_ID


@pytest.fixture
def client(hass, cloud) -> RenphoClient:
    return RenphoClient(async_get_clientsession(hass), EMAIL, PASSWORD)


def test_crypto_matches_the_app():
    # Vectors produced by the reference pycryptodome implementation.
    assert encrypt({}) == "b0LiByPBHmL5J19HjuIYDQ=="
    assert encrypt(b"") == "ZtDk/16Qik2UaElz2ZzmEg=="
    assert decrypt_bytes(encrypt({"a": "é"})) == b'{"a":"\\u00e9"}'


def test_timestamp_accepts_seconds_milliseconds_and_junk():
    assert timestamp({"timeStamp": 1_700_000_000}) == 1_700_000_000
    assert timestamp({"time_stamp": "1700000000000"}) == 1_700_000_000
    assert timestamp({"timeStamp": "soon"}) == 0
    assert timestamp({}) == 0


async def test_latest_measurement_reads_only_the_first_page(client, cloud):
    # The server lists newest first; a late-synced record may sit out of place.
    cloud.records = [{"timeStamp": 9000 - i, "weight": 70} for i in range(120)]
    cloud.records[3] = {"timeStamp": 9999, "weight": 81.5}

    assert await client.latest_measurement() == {"timeStamp": 9999, "weight": 81.5}
    assert client.user_id == USER_ID
    assert cloud.calls(MEASUREMENTS[0]) == 1
    assert cloud.calls(MEASUREMENTS[1]) == 0


async def test_weight_only_scale_falls_back_to_legacy_endpoint(client, cloud):
    cloud.legacy_only = True
    cloud.records = [{"timeStamp": 5, "weight": 60}]
    assert await client.latest_measurement() == {"timeStamp": 5, "weight": 60}


async def test_no_measurements_yet(client, cloud):
    assert await client.latest_measurement() is None


async def test_expired_token_logs_in_again(client, cloud):
    cloud.records = [{"timeStamp": 5, "weight": 60}]
    await client.latest_measurement()
    cloud.token = "token-2"  # server invalidates the old session

    assert await client.latest_measurement() == {"timeStamp": 5, "weight": 60}
    assert cloud.calls(LOGIN) == 2


async def test_token_is_reused_between_polls(client, cloud):
    await client.latest_measurement()
    await client.latest_measurement()
    assert cloud.calls(LOGIN) == 1


async def test_wrong_password(client, cloud):
    cloud.password = "changed"
    with pytest.raises(RenphoAuthError):
        await client.latest_measurement()


async def test_network_failure_is_not_an_auth_error(hass, aioclient_mock):
    aioclient_mock.post(BASE_URL + LOGIN, exc=aiohttp.ClientConnectionError())
    client = RenphoClient(async_get_clientsession(hass), EMAIL, PASSWORD)
    with pytest.raises(RenphoConnectionError):
        await client.login()


async def test_server_error_on_devices_falls_back_to_empty_object(hass, aioclient_mock):
    """A server that rejects the empty-bytes body still works via {}."""
    aioclient_mock.post(
        BASE_URL + LOGIN,
        json={"code": 0, "data": encrypt({"login": {"id": 1, "token": "t"}})},
    )
    seen = []

    async def devices(method, url, data):
        seen.append(decrypt_bytes(data["encryptData"]))
        if seen[-1] == b"":
            return Response(method, url, status=500)
        return Response(method, url, json={"code": 0, "data": encrypt({"scale": []})})

    aioclient_mock.post(BASE_URL + DEVICES, side_effect=devices)
    client = RenphoClient(async_get_clientsession(hass), EMAIL, PASSWORD)

    assert await client.latest_measurement() is None
    assert seen == [b"", b"{}"]
