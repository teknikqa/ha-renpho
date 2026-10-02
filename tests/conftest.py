"""A fake Renpho cloud that speaks the real encrypted wire format."""

from __future__ import annotations

import json

import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
    AiohttpClientMockResponse,
)

from custom_components.renpho_cloud.api import (
    BASE_URL,
    DEVICES,
    LOGIN,
    MEASUREMENTS,
    decrypt_bytes,
    encrypt,
)

EMAIL = "me@example.com"
PASSWORD = "hunter2"
USER_ID = "4242"
TABLE = "measurements_info_18"


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Let Home Assistant load custom_components/ in every test."""


class FakeCloud:
    """Stateful stand-in for cloud.renpho.com. Tests mutate its attributes."""

    def __init__(self, mocker: AiohttpClientMocker) -> None:
        self.mocker = mocker
        self.password = PASSWORD
        self.token = "token-1"
        self.records: list[dict] = []
        self.legacy_only = False  # serve records from the weight-only endpoint
        for path in (LOGIN, DEVICES, *MEASUREMENTS):
            mocker.post(BASE_URL + path, side_effect=self._handle)

    def calls(self, path: str) -> int:
        return sum(1 for call in self.mocker.mock_calls if call[1].path == "/" + path)

    def _reply(self, method, url, data=None, code=0, msg="success"):
        body = {"code": code, "msg": msg}
        if data is not None:
            body["data"] = encrypt(data)
        return AiohttpClientMockResponse(method, url, json=body)

    async def _handle(self, method, url, data):
        path = url.path.lstrip("/")
        raw = decrypt_bytes(data["encryptData"])
        headers = self.mocker.mock_calls[-1][3]

        if path == LOGIN:
            login = json.loads(raw)["login"]
            if (login["email"], login["password"]) != (EMAIL, self.password):
                return self._reply(method, url, code=40001, msg="password error")
            return self._reply(
                method, url, {"login": {"id": int(USER_ID), "token": self.token}}
            )

        if headers.get("token") != self.token or headers.get("userId") != USER_ID:
            return self._reply(method, url, code=401, msg="token expired")

        if path == DEVICES:
            if raw != b"":  # the app sends an encrypted empty body, not {}
                return AiohttpClientMockResponse(method, url, status=500)
            return self._reply(method, url, {"scale": [{"tableName": TABLE}]})

        query = json.loads(raw)
        assert query["tableName"] == TABLE
        assert query["userIds"] == [USER_ID]
        if self.legacy_only != (path == MEASUREMENTS[1]):
            return self._reply(method, url, [])
        start = (query["pageNum"] - 1) * query["pageSize"]
        return self._reply(method, url, self.records[start : start + query["pageSize"]])


@pytest.fixture
def cloud(aioclient_mock: AiohttpClientMocker) -> FakeCloud:
    return FakeCloud(aioclient_mock)
