from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

import allure
import pytest

from src.api_client import AvitoApiClient
from src.schemas import AuthorizeResponse, RegisterResponse
from tests.conftest import UserContext


@allure.feature("Авторизация и регистрация")
class TestAuth:
    @allure.title("TC-AUTH-01: Успешная регистрация нового пользователя")
    def test_register_success(self, api: AvitoApiClient) -> None:
        username = f"qa_reg_{uuid4().hex[:10]}"
        password = "StrongPassword123!"

        resp = api.register({"username": username, "password": password})
        assert resp.status_code == 201
        data = RegisterResponse.model_validate(resp.json())
        assert data.username == username
        assert data.id > 0

    @allure.title("TC-AUTH-02: Регистрация дубликата username возвращает 409")
    def test_register_duplicate_username(self, api: AvitoApiClient, auth_user: UserContext) -> None:
        resp = api.register({"username": auth_user.username, "password": "AnotherPassword123!"})
        assert resp.status_code == 409

    @allure.title("TC-AUTH-03: Регистрация с невалидными/пустыми данными возвращает 400")
    @pytest.mark.parametrize(
        "payload",
        [
            {"username": "", "password": ""},
            {"username": f"qa_{uuid4().hex[:6]}", "password": ""},
            {"username": "", "password": "StrongPassword123!"},
            {},
        ],
    )
    def test_register_invalid_payload(self, api: AvitoApiClient, payload: dict[str, str]) -> None:
        resp = api.register(payload)
        assert resp.status_code == 400

    @allure.title("TC-AUTH-04: Успешная авторизация возвращает Bearer JWT")
    def test_authorize_success(self, api: AvitoApiClient, auth_user: UserContext) -> None:
        resp = api.authorize({"username": auth_user.username, "password": auth_user.password})
        assert resp.status_code == 200
        data = AuthorizeResponse.model_validate(resp.json())
        assert data.tokenType == "Bearer"
        assert len(data.accessToken.split(".")) == 3

    @allure.title("TC-AUTH-05: Авторизация с неверным паролем или логином возвращает 401")
    @pytest.mark.parametrize("wrong_user,wrong_pass", [(False, True), (True, False)])
    def test_authorize_wrong_credentials(
        self,
        api: AvitoApiClient,
        auth_user: UserContext,
        wrong_user: bool,
        wrong_pass: bool,
    ) -> None:
        username = f"nonexistent_{uuid4().hex[:8]}" if wrong_user else auth_user.username
        password = "WrongPassword999!" if wrong_pass else auth_user.password

        resp = api.authorize({"username": username, "password": password})
        assert resp.status_code == 401

    @allure.title("TC-AUTH-06: Авторизация с некорректным телом запроса возвращает 400")
    def test_authorize_bad_request(self, api: AvitoApiClient) -> None:
        resp = api.authorize({})
        assert resp.status_code == 400

    @allure.title("TC-SEC-01: Защищённые ручки отклоняют запросы без Bearer-токена (401)")
    def test_protected_endpoints_without_token(
        self,
        api: AvitoApiClient,
        auth_user: UserContext,
        item_factory: Callable[..., tuple[str, dict]],
    ) -> None:
        item_id, payload = item_factory()

        responses = [
            api.create_item(payload, token=None),
            api.get_item(item_id, token=None),
            api.get_seller_items(auth_user.user_id, token=None),
            api.get_statistic_v1(item_id, token=None),
            api.get_statistic_v2(item_id, token=None),
            api.delete_item(item_id, token=None),
        ]
        for resp in responses:
            assert resp.status_code == 401, f"Ожидался 401 для {resp.request.method} {resp.url}"

    @allure.title("TC-SEC-02: Доступ с невалидным Bearer-токеном возвращает 401")
    def test_invalid_bearer_token(self, api: AvitoApiClient, auth_user: UserContext) -> None:
        resp = api.get_seller_items(auth_user.user_id, token="invalid.jwt.token")
        assert resp.status_code == 401
