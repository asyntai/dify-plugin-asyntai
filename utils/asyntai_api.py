"""Thin client for the Asyntai public API.

Every tool in this plugin goes through here, so the base URL, the auth header
and the error wording exist in exactly one place.
"""

from typing import Any

import requests

BASE_URL = "https://asyntai.com"
TIMEOUT = 60


class AsyntaiError(Exception):
    """An error the user can act on, already worded for the tool output."""


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "asyntai-dify-plugin/0.0.1",
    }


def _raise_for_status(response: requests.Response) -> None:
    """Turn an Asyntai error response into a message worth reading.

    The API answers 401 for a bad key and 403 when the plan has no API access.
    Both are settings problems, so they name the fix instead of the status code.
    """
    if response.status_code == 401:
        raise AsyntaiError(
            "Asyntai rejected the API key. Copy it again from "
            "https://asyntai.com/settings/ under API."
        )
    if response.status_code == 403:
        raise AsyntaiError(
            "The Asyntai API needs the Starter plan or higher. "
            "See https://asyntai.com/pricing/."
        )
    if response.status_code == 429:
        raise AsyntaiError(
            "This Asyntai account reached its monthly message limit."
        )

    if response.status_code >= 400:
        message = ""
        try:
            message = (response.json() or {}).get("error", "")
        except ValueError:
            message = ""
        raise AsyntaiError(
            message or f"Asyntai answered HTTP {response.status_code}."
        )


def _request(method: str, path: str, api_key: str, **kwargs: Any) -> dict[str, Any]:
    if not api_key:
        raise AsyntaiError("No Asyntai API key is set for this tool.")

    url = f"{BASE_URL}{path}"
    try:
        response = requests.request(
            method, url, headers=_headers(api_key), timeout=TIMEOUT, **kwargs
        )
    except requests.exceptions.Timeout:
        raise AsyntaiError("Asyntai did not answer in time. Try again.")
    except requests.exceptions.RequestException as exc:
        raise AsyntaiError(f"Could not reach Asyntai: {exc}")

    _raise_for_status(response)

    try:
        payload = response.json()
    except ValueError:
        raise AsyntaiError("Asyntai returned a response that is not JSON.")

    if not isinstance(payload, dict):
        raise AsyntaiError("Asyntai returned a response that is not an object.")

    # A 200 can still carry success=false, for example when a message limit is
    # hit, so the body decides as well as the status code.
    if payload.get("success") is False:
        raise AsyntaiError(payload.get("error") or "Asyntai reported a failure.")

    return payload


def get(path: str, api_key: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    clean = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    return _request("GET", path, api_key, params=clean)


def post(path: str, api_key: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    clean = {k: v for k, v in (body or {}).items() if v not in (None, "")}
    return _request("POST", path, api_key, json=clean)
