Патч интерфейса Auto Spa Detailing CRM.

Как установить на VPS:
1) Загрузить архив autospa_ui_patch.zip в /root/
2) Выполнить:
   cd /root/nextline_crm/nextline_crm_real
   cp -r app/templates app/templates_backup
   cp -r app/static app/static_backup
   unzip -o /root/autospa_ui_patch.zip -d /root/nextline_crm/nextline_crm_real
   docker compose down
   docker compose up -d --build
3) Открыть http://62.60.250.190:8000/
