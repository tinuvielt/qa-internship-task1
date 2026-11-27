cat << 'EOF' > BUGS.md
# Найденные баги API (`qa-internship`)

Стенд: `https://avito.com`  
Дефекты выявлены при прогоне автотестов из `tests/`.

---

## [BUG-API-01] Невозможно создать объявление с нулевой ценой (`price: 0`) — сервер отвечает 400 «поле price обязательно»
* **Серьёзность:** High (P1)
* **Endpoint:** `POST /api/1/item`
* **Связанный тест:** `tests/test_items.py::TestItems::test_create_item_zero_boundaries`
* **Шаги воспроизведения:**
  1. Зарегистрировать пользователя и получить валидный `Bearer` токен.
  2. Отправить `POST /api/1/item` с валидными данными, указав `"price": 0` (бесплатный товар / отдам даром):
     ```json
     {
       "sellerID": 12345,
       "name": "Test Item",
       "price": 0,
       "statistics": {"likes": 0, "viewCount": 0, "contacts": 0}
     }
     ```
* **Фактический результат:** сервер возвращает `400 Bad Request` с телом `{"result":{"message":"поле price обязательно","messages":{}},"status":"400"}` (вероятно, на бэкенде проверка наличия поля сделана через truthy/zero-value сравнение `price == 0`, а не `price == nil`).
* **Ожидаемый результат:** `200 OK`, объявление с ценой `0` успешно создаётся.

---

## [BUG-API-02] Валидация пропускает отрицательную цену (`price: -1`) при создании объявления
* **Серьёзность:** High (P1)
* **Endpoint:** `POST /api/1/item`
* **Связанный тест:** `tests/test_items.py::TestItems::test_create_item_invalid_values[override0]`
* **Шаги воспроизведения:**
  1. Авторизоваться и получить `Bearer` токен.
  2. Отправить `POST /api/1/item` с отрицательным значением цены `"price": -1`:
     ```json
     {
       "sellerID": 12345,
       "name": "Test Item",
       "price": -1,
       "statistics": {"likes": 1, "viewCount": 1, "contacts": 1}
     }
     ```
* **Фактический результат:** сервер возвращает `200 OK` и сохраняет объявление с отрицательной ценой (при этом для отрицательных значений в `statistics` сервер корректно отдаёт `400 Bad Request`).
* **Ожидаемый результат:** `400 Bad Request` с ошибкой валидации поля `price`.

---

## [BUG-API-03] Некорректный статус-код `404` вместо `400` при передаче невалидного UUID в ручку статистики v2
* **Серьёзность:** Low (P3)
* **Endpoint:** `GET /api/2/statistic/{id}`
* **Связанный тест:** `tests/test_statistics.py::TestStatistics::test_get_statistic_negative[invalid-uuid-400-v2]`
* **Шаги воспроизведения:**
  1. Авторизоваться и получить `Bearer` токен.
  2. Отправить запрос `GET /api/2/statistic/invalid-uuid` с валидным заголовком `Authorization: Bearer <token>`.
* **Фактический результат:** возвращается `404 Not Found` (тогда как `GET /api/1/statistic/invalid-uuid` и `GET /api/1/item/invalid-uuid` на тот же вход возвращают `400 Bad Request`).
* **Ожидаемый результат:** `400 Bad Request` из-за невалидного формата идентификатора UUID (единое поведение во всех версиях API).
EOF

