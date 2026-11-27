from __future__ import annotations

from collections.abc import Callable

import allure
import pytest

from src.api_client import AvitoApiClient
from src.schemas import StatisticsSchema
from tests.conftest import UserContext


@allure.feature("Статистика объявлений")
class TestStatistics:
    @allure.title("TC-STAT-01: Получение статистики v1 и v2 по существующему объявлению")
    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_get_statistic_success(
        self,
        api: AvitoApiClient,
        auth_user: UserContext,
        item_factory: Callable[..., tuple[str, dict]],
        version: str,
    ) -> None:
        item_id, payload = item_factory(likes=21, view_count=11, contacts=43)
        resp = (
            api.get_statistic_v1(item_id, token=auth_user.token)
            if version == "v1"
            else api.get_statistic_v2(item_id, token=auth_user.token)
        )
        assert resp.status_code == 200
        body = resp.json()
        stat_raw = body[0] if isinstance(body, list) else body
        stat = StatisticsSchema.model_validate(stat_raw)
        assert stat.model_dump() == payload["statistics"]

    @allure.title(
        "TC-STAT-02: Статистика v1 и v2 для несуществующего (404) и невалидного (400) UUID"
    )
    @pytest.mark.parametrize("version", ["v1", "v2"])
    @pytest.mark.parametrize(
        "item_id,expected_status",
        [
            ("00000000-0000-4000-8000-000000000000", 404),
            ("invalid-uuid", 400),
        ],
    )
    def test_get_statistic_negative(
        self,
        api: AvitoApiClient,
        auth_user: UserContext,
        version: str,
        item_id: str,
        expected_status: int,
    ) -> None:
        resp = (
            api.get_statistic_v1(item_id, token=auth_user.token)
            if version == "v1"
            else api.get_statistic_v2(item_id, token=auth_user.token)
        )
        assert resp.status_code == expected_status
