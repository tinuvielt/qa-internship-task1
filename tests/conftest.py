from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import pytest

from src.api_client import AvitoApiClient
from src.schemas import AuthorizeResponse, RegisterResponse


@dataclass
class UserContext:
    user_id: int
    username: str
    password: str
    token: str


@pytest.fixture(scope="session")
def api() -> AvitoApiClient:
    return AvitoApiClient()


@pytest.fixture(scope="session")
def user_factory(api: AvitoApiClient) -> Callable[[], UserContext]:
    def _create_user() -> UserContext:
        username = f"qa_mid_{uuid4().hex[:10]}"
        password = f"Pass_{uuid4().hex[:10]}!"

        reg_resp = api.register({"username": username, "password": password})
        assert reg_resp.status_code == 201, f"Ошибка регистрации: {reg_resp.text}"
        reg_data = RegisterResponse.model_validate(reg_resp.json())

        auth_resp = api.authorize({"username": username, "password": password})
        assert auth_resp.status_code == 200, f"Ошибка авторизации: {auth_resp.text}"
        auth_data = AuthorizeResponse.model_validate(auth_resp.json())

        return UserContext(
            user_id=reg_data.id,
            username=reg_data.username,
            password=password,
            token=auth_data.accessToken,
        )

    return _create_user


@pytest.fixture(scope="session")
def auth_user(user_factory: Callable[[], UserContext]) -> UserContext:
    return user_factory()


@pytest.fixture
def item_factory(
    api: AvitoApiClient, auth_user: UserContext
) -> Generator[Callable[..., tuple[str, dict[str, Any]]], None, None]:
    created_items: list[tuple[str, str]] = []

    def _create_item(
        name: str | None = None,
        price: int = 15000,
        likes: int = 5,
        view_count: int = 20,
        contacts: int = 2,
        user: UserContext | None = None,
    ) -> tuple[str, dict[str, Any]]:
        actor = user or auth_user
        payload = {
            "sellerID": actor.user_id,
            "name": name or f"Item_{uuid4().hex[:8]}",
            "price": price,
            "statistics": {
                "likes": likes,
                "viewCount": view_count,
                "contacts": contacts,
            },
        }
        resp = api.create_item(payload, token=actor.token)
        assert resp.status_code == 200, f"Не удалось создать объявление: {resp.text}"
        item_id = api.extract_item_id(resp)
        created_items.append((item_id, actor.token))
        return item_id, payload

    yield _create_item

    for item_id, token in created_items:
        api.delete_item(item_id, token=token)
