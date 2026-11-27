from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

import allure
import pytest

from src.api_client import AvitoApiClient
from src.schemas import CreateItemResponse, ItemSchema
from tests.conftest import UserContext


@allure.feature("Управление объявлениями")
class TestItems:
    @allure.title("TC-ITEM-01: Успешное создание объявления")
    def test_create_item_success(self, api: AvitoApiClient, auth_user: UserContext) -> None:
        payload = {
            "sellerID": auth_user.user_id,
            "name": f"QA Sofa {uuid4().hex[:6]}",
            "price": 25000,
            "statistics": {"likes": 10, "viewCount": 50, "contacts": 3},
        }
        resp = api.create_item(payload, token=auth_user.token)
        assert resp.status_code == 200
        CreateItemResponse.model_validate(resp.json())

        item_id = api.extract_item_id(resp)
        api.delete_item(item_id, token=auth_user.token)

    @allure.title("TC-ITEM-02: Два одинаковых объявления получают уникальные UUID")
    def test_create_duplicate_items_unique_uuids(
        self, item_factory: Callable[..., tuple[str, dict]]
    ) -> None:
        shared_name = f"SameItem_{uuid4().hex[:6]}"
        id_1, _ = item_factory(name=shared_name, price=1000, likes=1, view_count=2, contacts=3)
        id_2, _ = item_factory(name=shared_name, price=1000, likes=1, view_count=2, contacts=3)
        assert id_1 != id_2

    @allure.title("TC-ITEM-03 (positive): Нулевая цена и нулевая статистика валидны")
    def test_create_item_zero_boundaries(
        self,
        api: AvitoApiClient,
        auth_user: UserContext,
        item_factory: Callable[..., tuple[str, dict]],
    ) -> None:
        item_id, _ = item_factory(price=0, likes=0, view_count=0, contacts=0)
        resp = api.get_item(item_id, token=auth_user.token)
        assert resp.status_code == 200
        items = [ItemSchema.model_validate(obj) for obj in resp.json()]
        assert len(items) == 1
        assert items[0].price == 0
        assert items[0].statistics.likes == 0

    @allure.title("TC-ITEM-03/04 (negative): Отрицательные числа и невалидные поля возвращают 400")
    @pytest.mark.parametrize(
        "override",
        [
            {"price": -1},
            {"statistics": {"likes": -1, "viewCount": 0, "contacts": 0}},
            {"statistics": {"likes": 0, "viewCount": -1, "contacts": 0}},
            {"statistics": {"likes": 0, "viewCount": 0, "contacts": -1}},
            {"name": ""},
            {"price": "not_a_number"},
        ],
    )
    def test_create_item_invalid_values(
        self, api: AvitoApiClient, auth_user: UserContext, override: dict
    ) -> None:
        payload = {
            "sellerID": auth_user.user_id,
            "name": f"Item_{uuid4().hex[:6]}",
            "price": 5000,
            "statistics": {"likes": 1, "viewCount": 1, "contacts": 1},
            **override,
        }
        resp = api.create_item(payload, token=auth_user.token)
        assert resp.status_code == 400, f"Ожидался 400 для {override}, получено {resp.status_code}"

    @allure.title(
        "TC-SEC-03/04: Запрет создания объявления от имени другого sellerID или с X-UserId"
    )
    def test_create_item_foreign_seller_id_forbidden(
        self,
        api: AvitoApiClient,
        auth_user: UserContext,
        user_factory: Callable[[], UserContext],
    ) -> None:
        other_user = user_factory()
        payload = {
            "sellerID": other_user.user_id,
            "name": "Foreign Item",
            "price": 9999,
            "statistics": {"likes": 0, "viewCount": 0, "contacts": 0},
        }
        resp = api.create_item(
            payload,
            token=auth_user.token,
            extra_headers={"X-UserId": str(other_user.user_id)},
        )
        assert resp.status_code in (400, 401, 403)

    @allure.title("TC-ITEM-05: Получение объявления по UUID и сверка всех полей")
    def test_get_item_by_id_success(
        self,
        api: AvitoApiClient,
        auth_user: UserContext,
        item_factory: Callable[..., tuple[str, dict]],
    ) -> None:
        item_id, created_payload = item_factory(
            name="Диван QA 2026", price=25000, likes=7, view_count=42, contacts=4
        )
        resp = api.get_item(item_id, token=auth_user.token)
        assert resp.status_code == 200

        items = [ItemSchema.model_validate(obj) for obj in resp.json()]
        assert len(items) == 1
        item = items[0]
        assert item.id == item_id
        assert item.sellerId == auth_user.user_id
        assert item.name == created_payload["name"]
        assert item.price == created_payload["price"]
        assert item.statistics.model_dump() == created_payload["statistics"]

    @allure.title("TC-ITEM-06: Получение несуществующего (404) и невалидного (400) UUID")
    @pytest.mark.parametrize(
        "item_id,expected_status",
        [
            ("00000000-0000-4000-8000-000000000000", 404),
            ("invalid-uuid-123", 400),
        ],
    )
    def test_get_item_not_found_and_bad_request(
        self, api: AvitoApiClient, auth_user: UserContext, item_id: str, expected_status: int
    ) -> None:
        resp = api.get_item(item_id, token=auth_user.token)
        assert resp.status_code == expected_status

    @allure.title("TC-ITEM-07: Получение списка объявлений продавца")
    def test_get_seller_items(
        self,
        api: AvitoApiClient,
        user_factory: Callable[[], UserContext],
        item_factory: Callable[..., tuple[str, dict]],
    ) -> None:
        fresh_seller = user_factory()

        empty_resp = api.get_seller_items(fresh_seller.user_id, token=fresh_seller.token)
        assert empty_resp.status_code == 200
        assert empty_resp.json() == []

        id_1, _ = item_factory(user=fresh_seller)
        id_2, _ = item_factory(user=fresh_seller)

        list_resp = api.get_seller_items(fresh_seller.user_id, token=fresh_seller.token)
        assert list_resp.status_code == 200
        items = [ItemSchema.model_validate(obj) for obj in list_resp.json()]
        returned_ids = {item.id for item in items}
        assert {id_1, id_2} == returned_ids

    @allure.title("TC-ITEM-09: Удаление объявления и проверка 404 после удаления")
    def test_delete_item_flow(
        self,
        api: AvitoApiClient,
        auth_user: UserContext,
        item_factory: Callable[..., tuple[str, dict]],
    ) -> None:
        item_id, _ = item_factory()

        del_resp = api.delete_item(item_id, token=auth_user.token)
        assert del_resp.status_code == 200

        get_after_del = api.get_item(item_id, token=auth_user.token)
        assert get_after_del.status_code == 404

        second_del = api.delete_item(item_id, token=auth_user.token)
        assert second_del.status_code == 404
