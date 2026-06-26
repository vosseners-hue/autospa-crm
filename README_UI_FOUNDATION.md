# Auto Spa CRM UI Foundation

Этот коммит начинает переход от разрозненных шаблонов к единой дизайн-системе.

Добавлено:

- `templates/crm/components/sidebar.html` — боковое меню
- `templates/crm/components/topbar.html` — верхняя панель действий
- `templates/crm/components/messages.html` — системные уведомления
- `templates/crm/components/stat_card.html` — карточка статистики
- `templates/crm/components/panel_head.html` — заголовок панели

Зачем это нужно:

- меньше дублирования HTML;
- единый вид всех экранов;
- проще менять дизайн сразу во всей CRM;
- безопаснее развивать заказ-наряды, склад, календарь и аналитику.
