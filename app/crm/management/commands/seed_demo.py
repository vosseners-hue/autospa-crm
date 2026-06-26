from django.core.management.base import BaseCommand
from crm.models import *
class Command(BaseCommand):
    help='Создает демо-данные Next Line CRM'
    def handle(self,*args,**kwargs):
        shampoo,_=Material.objects.get_or_create(name='Шампунь', defaults={'unit':'ml','stock':5000,'cost':1.2,'min_stock':500})
        microfiber,_=Material.objects.get_or_create(name='Микрофибра', defaults={'unit':'pcs','stock':100,'cost':80,'min_stock':20})
        degreaser,_=Material.objects.get_or_create(name='Обезжириватель', defaults={'unit':'ml','stock':3000,'cost':2.5,'min_stock':400})
        polish,_=Material.objects.get_or_create(name='Полировальная паста', defaults={'unit':'ml','stock':2000,'cost':8,'min_stock':300})
        d1,_=Service.objects.get_or_create(name='Мойка D1 - экстерьер', defaults={'price':3000,'description':'Мойка кузова без салона'})
        d3,_=Service.objects.get_or_create(name='Мойка D3 - экстерьер + интерьер', defaults={'price':8000,'description':'Тщательная мойка кузова и салона'})
        pol,_=Service.objects.get_or_create(name='Полировка кузова', defaults={'price':45000})
        ServiceMaterial.objects.get_or_create(service=d1, material=shampoo, defaults={'qty':50})
        ServiceMaterial.objects.get_or_create(service=d1, material=microfiber, defaults={'qty':1})
        ServiceMaterial.objects.get_or_create(service=d3, material=shampoo, defaults={'qty':90})
        ServiceMaterial.objects.get_or_create(service=d3, material=microfiber, defaults={'qty':3})
        ServiceMaterial.objects.get_or_create(service=d3, material=degreaser, defaults={'qty':70})
        ServiceMaterial.objects.get_or_create(service=pol, material=polish, defaults={'qty':120})
        ServiceMaterial.objects.get_or_create(service=pol, material=degreaser, defaults={'qty':150})
        c,_=Customer.objects.get_or_create(name='Иван Петров', defaults={'phone':'+7 999 111-22-33','source':'Демо'})
        car,_=Car.objects.get_or_create(customer=c,brand='BMW',model='X5',plate='А001АА163',defaults={'year':2022,'color':'черный'})
        o,_=WorkOrder.objects.get_or_create(customer=c,car=car,status='new',defaults={'notes':'Демо заказ'})
        if not o.items.exists():
            WorkOrderItem.objects.create(order=o,service=d3,qty=1,price=d3.price)
            WorkOrderItem.objects.create(order=o,service=pol,qty=1,price=pol.price)
        self.stdout.write(self.style.SUCCESS('Демо-данные созданы'))
