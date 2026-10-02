"""Async client for the Renpho Health cloud API (cloud.renpho.com).

Unofficial. Every request and response body is AES-128-ECB encrypted with a
key baked into the mobile app, then base64-encoded.

No Home Assistant imports, so this file also runs standalone as a live check
that prints your latest raw measurement:

    RENPHO_EMAIL=... RENPHO_PASSWORD=... python api.py
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
from typing import Any

import aiohttp
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

BASE_URL = "https://cloud.renpho.com/"
LOGIN = "renpho-aggregation/user/login"
DEVICES = "renpho-aggregation/device/count"
# Impedance scales answer on the first endpoint, weight-only scales on the second.
MEASUREMENTS = (
    "RenphoHealth/scale/queryBodyCompositionMeasureData",
    "RenphoHealth/scale/queryAllMeasureDataList",
)

_KEY = b"ed*wijdi$h6fe3ew"  # app-wide key, not a user secret
_APP_VERSION = "6.6.0"
_PLATFORM = "android"
_SCALE_TYPES = [f"{i:02X}" for i in range(1, 21)]
_OK_CODES = {"0", "101", "200", "20000"}
_PAGE_SIZE = 50
_MAX_PAGES = 200  # 10,000 weigh-ins; stops a server that ignores pageNum
_TIMEOUT = aiohttp.ClientTimeout(total=30)


class RenphoError(Exception):
    """The API rejected a request or returned something unreadable."""


class RenphoConnectionError(RenphoError):
    """The cloud could not be reached."""


class RenphoAuthError(RenphoError):
    """The cloud rejected the email and password."""


def _cipher() -> Cipher[modes.ECB]:
    return Cipher(algorithms.AES(_KEY), modes.ECB())


def encrypt(payload: Any) -> str:
    """Encrypt a JSON-serialisable payload (or raw bytes) for the wire."""
    if not isinstance(payload, bytes):
        payload = json.dumps(payload, separators=(",", ":")).encode()
    padder = padding.PKCS7(128).padder()
    encryptor = _cipher().encryptor()
    padded = padder.update(payload) + padder.finalize()
    return base64.b64encode(encryptor.update(padded) + encryptor.finalize()).decode()


def decrypt_bytes(data: str) -> bytes:
    """Decrypt a wire string to raw bytes. Raises ValueError on bad input."""
    decryptor = _cipher().decryptor()
    unpadder = padding.PKCS7(128).unpadder()
    padded = decryptor.update(base64.b64decode(data)) + decryptor.finalize()
    return unpadder.update(padded) + unpadder.finalize()


def timestamp(record: dict[str, Any]) -> float:
    """Unix time of a measurement in seconds, or 0 if it has none."""
    try:
        ts = float(record.get("timeStamp") or record.get("time_stamp") or 0)
    except (TypeError, ValueError):
        return 0.0
    return ts / 1000 if ts > 1e11 else ts  # tolerate milliseconds


def _rows(data: Any) -> list[dict[str, Any]]:
    """Pull the record list out of a measurements page, whatever its wrapper."""
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    return [row for row in data if isinstance(row, dict)] if data else []


class RenphoClient:
    """One Renpho Health account. Logs in lazily and again when the token dies."""

    def __init__(
        self, session: aiohttp.ClientSession, email: str, password: str
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._token: str | None = None
        self.user_id: str | None = None

    async def _post(self, path: str, payload: Any, *, auth: bool = True) -> Any:
        headers = {}
        if auth:
            headers = {
                "token": self._token or "",
                "userId": self.user_id or "",
                "appVersion": _APP_VERSION,
                "platform": _PLATFORM,
            }
        try:
            resp = await self._session.post(
                BASE_URL + path,
                json={"encryptData": encrypt(payload)},
                headers=headers,
                timeout=_TIMEOUT,
            )
            if resp.status in (401, 403):
                raise RenphoError(f"{path}: HTTP {resp.status}")
            resp.raise_for_status()
            body = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise RenphoConnectionError(f"{path}: {err!r}") from err
        except ValueError as err:
            raise RenphoError(f"{path}: response is not JSON") from err

        if not isinstance(body, dict):
            raise RenphoError(f"{path}: unexpected response")
        code, msg = body.get("code"), str(body.get("msg", ""))
        if str(code) not in _OK_CODES and msg.lower() != "success":
            raise RenphoError(f"{path}: code={code} msg={msg}")
        data = body.get("data")
        if not data or not isinstance(data, str):
            return data
        try:
            return json.loads(decrypt_bytes(data))
        except ValueError as err:
            raise RenphoError(f"{path}: cannot decrypt response") from err

    async def login(self) -> None:
        """Exchange email and password for a session token."""
        payload = {
            "questionnaire": {},
            "login": {
                "email": self._email,
                "password": self._password,
                "areaCode": "US",
                "appRevision": _APP_VERSION,
                "cellphoneType": "HomeAssistant",
                "systemType": "11",
                "platform": _PLATFORM,
            },
            "bindingList": {"deviceTypes": _SCALE_TYPES},
        }
        try:
            data = await self._post(LOGIN, payload, auth=False)
        except RenphoConnectionError:
            raise
        except RenphoError as err:
            # ponytail: the bad-password code is undocumented, so any API-level
            # login rejection counts as bad credentials. Match the code if a
            # cloud-side fault ever triggers a false reauth prompt.
            raise RenphoAuthError(str(err)) from err
        info = data.get("login") if isinstance(data, dict) else None
        if not info or not info.get("token") or info.get("id") is None:
            raise RenphoAuthError("login response has no token")
        self._token = info["token"]
        self.user_id = str(info["id"])

    async def _call(self, path: str, payload: Any) -> Any:
        if self._token:
            try:
                return await self._post(path, payload)
            except RenphoConnectionError:
                raise
            except RenphoError:
                pass  # most likely an expired token: log in again and retry once
        await self.login()
        return await self._post(path, payload)

    async def _tables(self) -> set[str]:
        """Names of the server-side tables holding this user's measurements."""
        try:
            # The app sends an encrypted empty body here; some servers want {}.
            info = await self._call(DEVICES, b"")
        except RenphoAuthError:
            raise
        except RenphoError:
            info = await self._call(DEVICES, {})
        scales = info.get("scale") if isinstance(info, dict) else None
        return {s["tableName"] for s in scales or [] if s.get("tableName")}

    async def _records(self, table: str) -> list[dict[str, Any]]:
        for path in MEASUREMENTS:
            records: list[dict[str, Any]] = []
            for page in range(1, _MAX_PAGES + 1):
                rows = _rows(
                    await self._call(
                        path,
                        {
                            "pageNum": page,
                            "pageSize": _PAGE_SIZE,
                            "userIds": [self.user_id],
                            "tableName": table,
                        },
                    )
                )
                records += rows
                if len(rows) < _PAGE_SIZE:
                    break
            if records:
                return records
        return []

    async def latest_measurement(self) -> dict[str, Any] | None:
        """Return the newest measurement across all scales, or None."""
        # ponytail: reads the whole history every poll (one request per 50
        # weigh-ins) because the server's sort order is undocumented. Fetch
        # only page 1 once newest-first ordering is confirmed on a live account.
        records: list[dict[str, Any]] = []
        for table in await self._tables():
            records += await self._records(table)
        return max(records, key=timestamp, default=None)


async def _live_check() -> None:
    async with aiohttp.ClientSession() as session:
        client = RenphoClient(
            session, os.environ["RENPHO_EMAIL"], os.environ["RENPHO_PASSWORD"]
        )
        print(json.dumps(await client.latest_measurement(), indent=2))


if __name__ == "__main__":
    asyncio.run(_live_check())
