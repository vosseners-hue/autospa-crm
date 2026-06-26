# Next Line CRM MVP

Рабочая первая версия CRM для детейлинг-центра.

## Запуск на VPS

```bash
apt update
apt install -y docker.io docker-compose-v2 unzip
unzip nextline_crm_real.zip -d nextline_crm
cd nextline_crm
cp .env.example .env
nano .env
```

В `.env` укажи IP VPS в `ALLOWED_HOSTS`.

Запуск:

```bash
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_demo
```

Открыть:

```text
http://IP_ТВОЕГО_VPS:8000/
```

Админка:

```text
http://IP_ТВОЕГО_VPS:8000/admin/
```

## Что есть
- Клиенты
- Автомобили
- Услуги
- Заказ-наряды
- PDF заказ-наряда
- Склад материалов
- Нормы расхода материалов на услуги
- Списание материалов со склада
- Простая статистика
