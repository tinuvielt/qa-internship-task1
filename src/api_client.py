from __future__ import annotations

import json
import re
from typing import Any

import allure
import requests

UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
    re.IGNORECASE,
)


class AvitoApiClient:
    def __init__(self, base_url: str = "https://qa-internship.avito.com") -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _request(
        self,
        method: str,
        endpoint: str,
        token: str | None = None,
        extra_headers: dict[str, str] | None = None,
        json_body: Any = None,
    ) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if extra_headers:
            headers.update(extra_headers)

        with allure.step(f"{method} {endpoint}"):
            if json_body is not None:
                allure.attach(
                    json.dumps(json_body, ensure_ascii=False, indent=2),
                    name="Request Body",
                    attachment_type=allure.attachment_type.JSON,
                )
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_body,
                timeout=15,
            )
            allure.attach(
                f"Status: {response.status_code}\nBody: {response.text}",
                name="Response",
                attachment_type=allure.attachment_type.TEXT,
            )
            return response

    def register(self, payload: dict[str, Any]) -> requests.Response:
        return self._request("POST", "/api/1/register", json_body=payload)

    def authorize(self, payload: dict[str, Any]) -> requests.Response:
        return self._request("POST", "/api/1/autorize", json_body=payload)

    def create_item(
        self,
        payload: dict[str, Any],
        token: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> requests.Response:
        return self._request(
            "POST",
            "/api/1/item",
            token=token,
            extra_headers=extra_headers,
            json_body=payload,
        )

    def get_item(self, item_id: str, token: str | None = None) -> requests.Response:
        return self._request("GET", f"/api/1/item/{item_id}", token=token)

    def get_seller_items(self, seller_id: int | str, token: str | None = None) -> requests.Response:
        return self._request("GET", f"/api/1/{seller_id}/item", token=token)

    def get_statistic_v1(self, item_id: str, token: str | None = None) -> requests.Response:
        return self._request("GET", f"/api/1/statistic/{item_id}", token=token)

    def get_statistic_v2(self, item_id: str, token: str | None = None) -> requests.Response:
        return self._request("GET", f"/api/2/statistic/{item_id}", token=token)

    def delete_item(self, item_id: str, token: str | None = None) -> requests.Response:
        return self._request("DELETE", f"/api/2/item/{item_id}", token=token)

    @staticmethod
    def extract_item_id(response: requests.Response) -> str:
        body = response.json()
        match = UUID_PATTERN.search(str(body.get("status", "")))
        assert match, f"UUID не найден в ответе: {body}"
        return match.group(0)
