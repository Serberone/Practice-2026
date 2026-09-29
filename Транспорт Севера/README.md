# Транспорт Севера

Веб-приложение: расписание и транспорт (практика 2026).

- **Backend:** Python + FastAPI + MongoDB  
- **Frontend:** React  
- **Расписание:** API Яндекс.Расписаний (ключ в `.env`)

Документация: [`../Док-я/`](../Док-я/README.md).

## Локальная настройка секретов

```bash
cp .env.example .env
# задай YANDEX_RASP_API_KEY в .env
```

Файл `.env` не коммитится.

## Структура (заготовка)

- `backend/` — FastAPI  
- `frontend/` — React  
