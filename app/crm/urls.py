from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reception/', views.reception, name='reception'),
    path('reception/create-order/', views.reception_create_order, name='reception_create_order'),

    path('booking/', views.booking, name='booking'),
    path('booking/add/', views.booking_create, name='booking_create'),
    path('booking/<int:pk>/edit/', views.booking_update, name='booking_update'),
    path('booking/<int:pk>/delete/', views.booking_delete, name='booking_delete'),
    path('booking/<int:pk>/create-order/', views.booking_create_order, name='booking_create_order'),

    path('customers/', views.customers, name='customers'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_update, name='customer_update'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    path('cars/', views.cars, name='cars'),
    path('cars/add/', views.car_create, name='car_create'),
    path('cars/<int:pk>/', views.car_detail, name='car_detail'),
    path('cars/<int:pk>/edit/', views.car_update, name='car_update'),
    path('cars/<int:pk>/delete/', views.car_delete, name='car_delete'),

    path('services/', views.services, name='services'),
    path('services/add/', views.service_create, name='service_create'),
    path('services/<int:pk>/edit/', views.service_update, name='service_update'),
    path('services/<int:pk>/delete/', views.service_delete, name='service_delete'),

    path('inventory/', views.inventory, name='inventory'),
    path('inventory/add/', views.material_create, name='material_create'),
    path('inventory/<int:pk>/edit/', views.material_update, name='material_update'),
    path('inventory/<int:pk>/delete/', views.material_delete, name='material_delete'),

    path('stock-movements/', views.stock_movements, name='stock_movements'),
    path('stock-movements/add/', views.stock_movement_create, name='stock_movement_create'),

    path('orders/', views.orders, name='orders'),
    path('orders/add/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/edit/', views.order_update, name='order_update'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('orders/<int:pk>/inspection/', views.order_inspection, name='order_inspection'),
    path('orders/<int:pk>/inspection/damages/<int:damage_id>/delete/', views.order_damage_delete, name='order_damage_delete'),
    path('orders/<int:pk>/inspection/photos/<int:photo_id>/delete/', views.order_photo_delete, name='order_photo_delete'),
    path('orders/<int:pk>/writeoff/', views.order_writeoff, name='order_writeoff'),
    path('orders/<int:pk>/close/', views.order_close, name='order_close'),
    path('orders/<int:pk>/print/', views.order_print, name='order_print'),
    path('orders/<int:pk>/pdf/', views.order_pdf, name='order_pdf'),
]
