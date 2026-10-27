# Онлайн-табло «Транспорт Севера» (Республика Коми)

Веб-приложение для мониторинга междугородних автобусов и авиарейсов с интеграцией метеоданных и автоматическим расчётом задержек в сложных климатических условиях Крайнего Севера (Сыктывкар, Ухта, Усинск, Печора).

## 🚀 Архитектура и стек технологий

| Компонент | Стек | Описание |
|-----------|------|----------|
| **Backend** | Python 3.11, FastAPI, Pydantic v2 | Асинхронный REST API, JWT-аутентификация (RBAC: Пассажир, Диспетчер, Администратор), аудит-лог, автооценка метеоугроз |
| **Frontend** | React 18, Vite | Адаптивное онлайн-табло, фильтры, поиск, модальные окна деталей рейса, подписки на уведомления, панели диспетчера и администратора |
| **База данных** | MongoDB 6+ (Motor / PyMongo) | Хранение станций, перевозчиков, рейсов, метеологов, подписок, уведомлений и аудита (с отказоустойчивым in-memory fallback режимом для локального демо без БД) |
| **Внешние API** | Яндекс.Расписания v3 (квота 500 запр/сут с кэшем), Open-Meteo / Метеомодель Севера | Расписание рейсов, мониторинг метели, шквального ветра, гололёда и видимости |

---

## 🛠️ Локальный запуск

### Вариант 1: Запуск через Docker Compose (рекомендуется)

```bash
cd Transport_severa
docker-compose up --build
```
* **Frontend:** http://localhost:3000
* **Backend API & Swagger:** http://localhost:8000/docs
* **MongoDB:** `localhost:27017`
* Логин идёт на `POST /api/auth/login` (nginx проксирует на бэкенд).

### Вариант 2: Запуск без Docker

#### 1. Backend
```bash
cd Transport_severa/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*(Приложение автоматически инициализирует тестовые данные по Республике Коми: города Сыктывкар, Усинск, Ухта, Печора, перевозчики Комиавиатранс, КомиАвтотранс, РусЛайн, СеверТрансАвто).*

#### 2. Frontend
```bash
cd Transport_severa/frontend
npm install
npm run dev
```
Vite проксирует `/api` на `http://localhost:8000`. Не задавай `VITE_API_BASE_URL` локально, если бэкенд на том же порту 8000.

---

## ☁️ Развёртывание на бесплатном хостинге (Free Tier)

Сервис полностью оптимизирован для бесплатного размещения:

1. **База данных — MongoDB Atlas (M0 Free Tier, 512 МБ навсегда бесплатно):**
   * Зарегистрируйтесь на [mongodb.com/atlas](https://www.mongodb.com/atlas).
   * Создайте бесплатный кластер `M0 Sandbox` в регионе Frankfurt (AWS/GCP).
   * В разделе *Database Access* создайте пользователя (логин и пароль).
   * В разделе *Network Access* разрешите подключения со всех IP (`0.0.0.0/0`).
   * Скопируйте строку подключения `mongodb+srv://...` и укажите её в переменной `MONGODB_URI`.

2. **Backend API — Render.com (Free Web Service):**
   * Создайте репозиторий на GitHub и загрузите проект.
   * На [render.com](https://render.com) нажмите **New + -> Web Service**.
   * Выберите репозиторий, укажите:
     * **Root Directory:** `backend`
     * **Runtime:** Python
     * **Build Command:** `pip install -r requirements.txt`
     * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
     * **Environment Variables:**
       * `MONGODB_URI`: строка от MongoDB Atlas
       * `MONGODB_DB_NAME`: `transport_severa`
       * `YANDEX_RASP_API_KEY`: ваш ключ API (если есть)
       * `CORS_ORIGINS`: `["*"]`

3. **Frontend — Vercel / Netlify / Render Static Site:**
   * На [vercel.com](https://vercel.com) импортируйте репозиторий:
     * **Root Directory:** `frontend`
     * **Framework Preset:** Vite
     * **Environment Variables (обязательно на этапе Build):**  
       `VITE_API_BASE_URL` = `https://<имя-бэкенда>.onrender.com/api`  
       Пример: `https://transport-severa-backend.onrender.com/api`
   * Нужны и `https://`, и суффикс `/api`. Иначе логин уйдёт на `/auth/login` или на сам фронт и вернёт **404**.
   * После смены переменной пересобери фронт: Vite подставляет URL только при `npm run build`.
   * На Render Free первый запрос к бэкенду после сна может идти 30–60 секунд.

---

## 👥 Тестовые учётные записи

* **Диспетчер:** логин `dispatcher`, пароль `disp123`
* **Администратор:** логин `admin`, пароль `admin123`
