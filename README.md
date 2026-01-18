# Freelance Cashflow Predictor

Веб-сервис для учёта доходов фрилансера: хранение инвойсов, импорт CSV, аналитика и прогноз месячного cashflow.

**Ссылка на рабочий проект:** https://your-username.pythonanywhere.com  (заменить на реальную ссылку)

## Технологии
* Python 3.10–3.11
* Django 4.2.x
* Chart.js (frontend)
* Bootstrap 5

## Функционал
* Регистрация/авторизация
* CRUD: Clients, Projects, Categories, Invoices
* Импорт CSV (веб-форма + management command)
* Дашборд с историей и прогнозом (Chart.js / Plotly)
* Экспорт инвойсов в CSV

## Минимальные системные требования
* Python 3.10 или 3.11
* Для деплоя на PythonAnywhere: учитывать ограничение по диску/памяти, при необходимости используйте вариант без Pandas/scikit-learn.

## Как запустить проект локально
1. Клонировать репозиторий:
   ```bash
    git clone https://github.com/ВАШ/РЕПО.git
    cd РЕПО
2. Создать и активировать виртуальное окружение:
    ```bash
    python -m venv venv
    venv\Scripts\activate      # Windows
    source venv/bin/activate
3. Установить зависимости:
   ```bash
   3.Установить зависимости:
4. Выполнить миграции и создать суперпользователя:
    ```bash
    python manage.py migrate
    python manage.py createsuperuser
5. Запустить сервер:
    ```bash
   python manage.py runserver
6. Открыть в браузере: http://127.0.0.1:8000/