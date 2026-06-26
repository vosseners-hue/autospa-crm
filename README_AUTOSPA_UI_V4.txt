Auto Spa Detailing CRM UI Patch v4

Что добавлено:
- красивые формы добавления/редактирования без перехода в Django Admin;
- страницы: клиент, автомобиль, услуга, материал, движение склада, заказ-наряд;
- кнопки меню и быстрых действий теперь ведут на красивые страницы сайта;
- Django Admin остается только для технических настроек по адресу /admin/.

Установка:
cd /root/nextline_crm/nextline_crm_real
unzip -o /root/autospa_ui_patch_v4.zip -d /root/nextline_crm/nextline_crm_real
docker compose down
docker compose up -d --build

После установки используйте:
/customers/add/
/cars/add/
/services/add/
/inventory/add/
/stock-movements/add/
/orders/add/
