Отлично. Для MVP это даже лучше — архитектура становится значительно проще, а стоимость поддержки ниже. Тогда техническое задание нужно скорректировать следующим образом.

# Обновленный технологический стек

## Backend

* Python 3.12+
* FastAPI
* Uvicorn
* Pydantic v2
* OpenAI SDK

## Frontend

* Streamlit

## База данных

Единственная БД:

SQLite

Используется для хранения:

* пользовательских профилей;
* истории запросов;
* истории рекомендаций;
* обратной связи пользователей;
* настроек приложения.

---

# Исключенные технологии

Из проекта исключаются:

* Redis
* PostgreSQL
* Docker
* Kubernetes
* Prometheus
* Grafana

Причина:

Для MVP не предполагается высокая нагрузка, поэтому использование дополнительных инфраструктурных компонентов приводит к неоправданному усложнению проекта.

---

# Архитектурный подход

Вместо полноценного DDD предлагается использовать упрощенную модульную архитектуру.

Принципы:

* разделение ответственности;
* слабая связанность компонентов;
* возможность дальнейшего масштабирования;
* возможность замены LLM без изменения бизнес-логики.

---

# Структура проекта

```text
project/

│
├── .env
│
├── api/
│   ├── recommendations.py
│   ├── profile.py
│   ├── feedback.py
│   └── healthcheck.py
│
├── services/
│   ├── recommendation_service.py
│   ├── profile_service.py
│   ├── feedback_service.py
│   └── prompt_builder_service.py
│
├── llm/
│   ├── base_provider.py
│   ├── openai_provider.py
│   ├── prompts.py
│   └── schemas.py
│
├── config/
│   ├── settings.py
│   ├── database.py
│   └── logging.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── streamlit_app.py
│
├── requirements.txt
│
└── main.py
```

---

# Назначение директорий

## /.env

Хранение конфигурации среды.

Пример:

```env
OPENAI_API_KEY=
MODEL_NAME=gpt-5.5-mini
DATABASE_URL=sqlite:///app.db
```

---

## /api

Содержит REST-endpoints.

Ответственность:

* прием запросов;
* валидация данных;
* возврат ответов;
* обработка ошибок.

Пример:

```python
POST /recommendation
GET /history
POST /feedback
```

---

## /services

Основной слой бизнес-логики.

Никаких обращений к FastAPI внутри сервисов.

Задачи:

* формирование рекомендаций;
* работа с историей;
* работа с профилем;
* подготовка контекста для LLM;
* обработка ответов модели.

---

## /llm

Изолированный слой работы с языковыми моделями.

Цель:

Чтобы в будущем можно было заменить OpenAI на другого провайдера без изменения бизнес-логики.

### base_provider.py

Абстрактный интерфейс:

```python
class BaseLLMProvider:
    async def generate(self, prompt: str):
        pass
```

---

### openai_provider.py

Реализация OpenAI API.

Отвечает за:

* подключение;
* вызов модели;
* обработку ошибок;
* возврат результата.

---

### prompts.py

Хранение системных промптов.

Например:

```python
SYSTEM_PROMPT
FOLLOWUP_PROMPT
RECOMMENDATION_PROMPT
```

---

### schemas.py

Pydantic-схемы для работы с LLM.

Пример:

```python
RecommendationResponse
FollowupQuestion
```

---

## /config

Конфигурационный слой.

---

### settings.py

Загрузка переменных окружения.

```python
OPENAI_API_KEY
MODEL_NAME
DATABASE_URL
```

---

### database.py

Подключение к SQLite.

Создание:

```python
engine
session
```

---

### logging.py

Настройка логирования.

Уровни:

* INFO
* WARNING
* ERROR

---

# Бизнес-логика формирования рекомендации

## Шаг 1

Пользователь вводит запрос.

Например:

> Не знаю, как провести субботу.

---

## Шаг 2

RecommendationService анализирует запрос.

---

## Шаг 3

Если данных недостаточно:

LLM генерирует уточняющие вопросы.

Например:

* Какой бюджет?
* Один или с компанией?
* Любите активный отдых?

---

## Шаг 4

После получения контекста строится финальный промпт.

---

## Шаг 5

Вызов OpenAI.

---

## Шаг 6

Возврат структурированного ответа.

Формат:

```json
{
  "main_recommendation": "",
  "alternatives": [],
  "reasoning": "",
  "budget_estimation": "",
  "time_estimation": ""
}
```

---

# Модель данных SQLite

## recommendations

```sql
id INTEGER PRIMARY KEY
user_query TEXT
context TEXT
recommendation TEXT
created_at DATETIME
```

---

## feedback

```sql
id INTEGER PRIMARY KEY
recommendation_id INTEGER
rating INTEGER
comment TEXT
created_at DATETIME
```

---

## user_profile

```sql
id INTEGER PRIMARY KEY
budget TEXT
activity_level TEXT
favorite_activities TEXT
disliked_activities TEXT
created_at DATETIME
```

---

# Тестирование

## Unit Tests

Покрывают:

* RecommendationService
* PromptBuilderService
* OpenAIProvider (mock)

---

## Integration Tests

Покрывают:

* FastAPI endpoints
* SQLite взаимодействие
* полный сценарий обращения к сервисам

---

# MVP-результат

После завершения разработки пользователь сможет:

1. Открыть Streamlit-интерфейс.
2. Описать свою ситуацию.
3. Ответить на уточняющие вопросы AI.
4. Получить персональную рекомендацию.
5. Посмотреть альтернативы.
6. Сохранить историю рекомендаций.
7. Оценить качество предложенного варианта отдыха.

Жду структуру данных, которую ты хочешь использовать. После этого можно будет сформировать финальную версию ТЗ уровня Solution Design Document (SDD) с UML-диаграммами, sequence diagram, ER-диаграммой SQLite и описанием всех API-контрактов.
