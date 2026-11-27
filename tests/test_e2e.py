from __future__ import annotations

from uuid import uuid4

import allure

from src.api_client import AvitoApiClient
from src.schemas import AuthorizeResponse, ItemSchema, RegisterResponse, StatisticsSchema


@allure.feature("E2E сценарии")
@allure.title("TC-E2E-01: Полный жизненный цикл пользователя и объявления")
def test_full_item_lifecycle_e2e(api: AvitoApiClient) -> None:
    username = f"e2e_user_{uuid4().hex[:10]}"
    password = f"E2ePass_{uuid4().hex[:8]}!"

    # 1. Регистрация
    reg_resp = api.register({"username": username, "password": password})
    assert reg_resp.status_code == 201
    user = RegisterResponse.model_validate(reg_resp.json())

    # 2. Авторизация
    auth_resp = api.authorize({"username": username, "password": password})
    assert auth_resp.status_code == 200
    token = AuthorizeResponse.model_validate(auth_resp.json()).accessToken

    # 3. Создание объявления
    payload = {
        "sellerID": user.id,
        "name": "E2E Диван угловой QA 2026",
        "price": 25000,
        "statistics": {"likes": 15, "viewCount": 120, "contacts": 8},
    }
    create_resp = api.create_item(payload, token=token)
    assert create_resp.status_code == 200
    item_id = api.extract_item_id(create_resp)

    # 4. Получение объявления по ID
    get_resp = api.get_item(item_id, token=token)
    assert get_resp.status_code == 200
    items = [ItemSchema.model_validate(obj) for obj in get_resp.json()]
    assert len(items) == 1
    assert items[0].id == item_id
    assert items[0].name == payload["name"]

    # 5. Получение списка объявлений продавца
    seller_items_resp = api.get_seller_items(user.id, token=token)
    assert seller_items_resp.status_code == 200
    assert any(obj["id"] == item_id for obj in seller_items_resp.json())

    # 6. Получение статистики v1 и v2
    stat_v1_resp = api.get_statistic_v1(item_id, token=token)
    assert stat_v1_resp.status_code == 200
    stat_v1_body = stat_v1_resp.json()
    stat_v1_raw = stat_v1_body[0] if isinstance(stat_v1_body, list) else stat_v1_body
    assert StatisticsSchema.model_validate(stat_v1_raw).model_dump() == payload["statistics"]

    stat_v2_resp = api.get_statistic_v2(item_id, token=token)
    assert stat_v2_resp.status_code == 200

    # 7. Удаление объявления
    del_resp = api.delete_item(item_id, token=token)
    assert del_resp.status_code == 200

    # 8. Проверка, что объявление удалено
    check_deleted_resp = api.get_item(item_id, token=token)
    assert check_deleted_resp.status_code == 404
