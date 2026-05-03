"""
Finai Agent Auth Module
Handle authentication dan API calls ke kayakaga-api
"""

import os
import requests
from datetime import datetime, timedelta

API_URL = os.getenv("FINAI_API_URL", "http://localhost:8080")

_access_token = None
_token_expires_at = None


def get_token() -> str:
    """Get valid access token, auto-login jika belum ada atau expired."""
    global _access_token, _token_expires_at

    if _access_token and _token_expires_at and datetime.now() < _token_expires_at:
        return _access_token

    return _login()


def _login() -> str:
    """Login ke API dan dapatkan access token."""
    global _access_token, _token_expires_at

    response = requests.post(
        f"{API_URL}/api/v1/auth/login",
        json={
            "email": os.getenv("FINAI_API_EMAIL"),
            "password": os.getenv("FINAI_API_PASSWORD")
        },
        timeout=10
    )

    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")

    data = response.json()["data"]
    _access_token = data["access_token"]
    # Access token expire 15 menit, refresh 1 menit sebelumnya
    _token_expires_at = datetime.now() + timedelta(minutes=14)

    return _access_token


def get_headers() -> dict:
    """Get headers dengan authorization token."""
    return {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json"
    }


def api_get(endpoint: str, params: dict = None) -> dict:
    """
    Helper untuk GET request ke API.

    Args:
        endpoint: API endpoint path (contoh: "/api/v1/transactions")
        params: Query parameters (optional)

    Returns:
        Data dari response API, atau dict dengan error key
    """
    response = requests.get(
        f"{API_URL}{endpoint}",
        headers=get_headers(),
        params=params,
        timeout=10
    )

    if not response.ok:
        return {"error": f"API error {response.status_code}: {response.text}"}

    return response.json().get("data", {})
