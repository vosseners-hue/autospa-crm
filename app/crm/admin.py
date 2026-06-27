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
class WorkOrderItemInline(admin.TabularInline):
    model=WorkOrderItem
    extra=1
    fields=('service','qty','price','line_discount','comment','total')
    readonly_fields=('total',)
@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin): list_display=('number','customer','car','status','date_in','total','materials_written_off'); inlines=[WorkOrderItemInline]; readonly_fields=('number','materials_written_off')
@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin): list_display=('material','qty','unit_cost','order','created_at')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display=('start_at','customer','car','service','status','order')
    list_filter=('status','start_at')
    search_fields=('customer__name','customer__phone','car__brand','car__model','car__plate','car__vin')

class VehicleDamageInline(admin.TabularInline):
    model=VehicleDamage
    extra=0

@admin.register(VehicleInspection)
class VehicleInspectionAdmin(admin.ModelAdmin):
    list_display=('order','mileage','fuel_level','updated_at')
    search_fields=('order__number','order__customer__name','order__car__plate','order__car__vin')
    inlines=[VehicleDamageInline]

@admin.register(WorkOrderPhoto)
class WorkOrderPhotoAdmin(admin.ModelAdmin):
    list_display=('order','photo_type','comment','created_at')
    list_filter=('photo_type','created_at')
