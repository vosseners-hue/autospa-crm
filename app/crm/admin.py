from django.contrib import admin
from .models import *
class CarInline(admin.TabularInline): model=Car; extra=0
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin): list_display=('name','phone','source','created_at'); search_fields=('name','phone'); inlines=[CarInline]
@admin.register(Car)
class CarAdmin(admin.ModelAdmin): list_display=('brand','model','plate','customer'); search_fields=('brand','model','plate','vin')
class ServiceMaterialInline(admin.TabularInline): model=ServiceMaterial; extra=1
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin): list_display=('name','price','active'); inlines=[ServiceMaterialInline]
@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin): list_display=('name','stock','unit','cost','min_stock'); search_fields=('name',)
class WorkOrderItemInline(admin.TabularInline): model=WorkOrderItem; extra=1
@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin): list_display=('number','customer','car','status','date_in','total','materials_written_off'); inlines=[WorkOrderItemInline]; readonly_fields=('number','materials_written_off')
@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin): list_display=('material','qty','unit_cost','order','created_at')
