# Тестовое задание QA (осень 2026)

В репозитории собраны решения обеих частей задания:
* `BUGS_TASK1.md` — разбор багов со скриншотов из Задания 1.
* `TESTCASES.md` — тест-кейсы к API (Задание 2.1).
* `BUGS.md` — баги стенда, которые нашлись при прогоне автотестов.
* `PROMPTS.md` — промпты, которые использовались при работе с ИИ.
* `src/` и `tests/` — автотесты на Python (`pytest`, `requests`, `pydantic`, `allure`).

## Как запустить

Понадобится Python 3.8+.

1. Поднимаем окружение и ставим зависимости:
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Запускаем тесты:
```bash
pytest
```

3. Если установлен Allure CLI, можно открыть отчёт:
```bash
allure serve allure-results
```

4. Проверка линтером и форматтером (Ruff):
```bash
ruff check .
ruff format --check .
```

