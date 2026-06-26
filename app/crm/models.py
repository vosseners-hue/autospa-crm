from django.db import models, transaction
from django.urls import reverse

class Customer(models.Model):
    name=models.CharField('Имя клиента', max_length=160)
    phone=models.CharField('Телефон', max_length=60, blank=True)
    messenger=models.CharField('WhatsApp/Telegram', max_length=120, blank=True)
    source=models.CharField('Источник', max_length=120, blank=True)
    notes=models.TextField('Комментарий', blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Car(models.Model):
    customer=models.ForeignKey(Customer,on_delete=models.CASCADE,related_name='cars', verbose_name='Клиент')
    brand=models.CharField('Марка', max_length=80)
    model=models.CharField('Модель', max_length=80)
    year=models.PositiveIntegerField('Год', null=True, blank=True)
    plate=models.CharField('Госномер', max_length=40, blank=True)
    vin=models.CharField('VIN', max_length=40, blank=True)
    color=models.CharField('Цвет', max_length=80, blank=True)
    def __str__(self): return f'{self.brand} {self.model} {self.plate}'.strip()

class Service(models.Model):
    name=models.CharField('Услуга', max_length=160)
    price=models.DecimalField('Цена', max_digits=12, decimal_places=2, default=0)
    description=models.TextField('Описание', blank=True)
    active=models.BooleanField('Активна', default=True)
    def __str__(self): return self.name

class Material(models.Model):
    UNIT_CHOICES=[('ml','мл'),('l','л'),('m2','м²'),('pcs','шт'),('g','г'),('kg','кг')]
    name=models.CharField('Материал', max_length=160)
    unit=models.CharField('Ед. изм.', max_length=20, choices=UNIT_CHOICES, default='pcs')
    stock=models.DecimalField('Остаток', max_digits=12, decimal_places=3, default=0)
    cost=models.DecimalField('Себестоимость за ед.', max_digits=12, decimal_places=2, default=0)
    min_stock=models.DecimalField('Минимальный остаток', max_digits=12, decimal_places=3, default=0)
    def __str__(self): return f'{self.name} ({self.stock} {self.get_unit_display()})'

class ServiceMaterial(models.Model):
    service=models.ForeignKey(Service,on_delete=models.CASCADE,related_name='norms')
    material=models.ForeignKey(Material,on_delete=models.CASCADE)
    qty=models.DecimalField('Норма расхода', max_digits=12, decimal_places=3)
    class Meta: unique_together=('service','material')
    def __str__(self): return f'{self.service} -> {self.material}: {self.qty}'

class WorkOrder(models.Model):
    STATUS=[('new','Принят'),('work','В работе'),('ready','Готов'),('done','Выдан'),('cancel','Отменен')]
    number=models.CharField('Номер', max_length=30, unique=True, blank=True)
    customer=models.ForeignKey(Customer,on_delete=models.PROTECT, verbose_name='Клиент')
    car=models.ForeignKey(Car,on_delete=models.PROTECT, verbose_name='Авто')
    status=models.CharField('Статус', max_length=20, choices=STATUS, default='new')
    date_in=models.DateTimeField('Дата приема', auto_now_add=True)
    planned_out=models.DateTimeField('План выдачи', null=True, blank=True)
    discount=models.DecimalField('Скидка', max_digits=12, decimal_places=2, default=0)
    notes=models.TextField('Комментарий', blank=True)
    materials_written_off=models.BooleanField(default=False)
    def save(self,*args,**kwargs):
        if not self.number:
            last=WorkOrder.objects.order_by('-id').first()
            n=(last.id+1) if last else 1
            self.number=f'ZN-{n:06d}'
        super().save(*args,**kwargs)
    @property
    def subtotal(self): return sum([i.total for i in self.items.all()])
    @property
    def total(self): return max(self.subtotal - self.discount, 0)
    @property
    def material_cost(self): return sum([m.total_cost for m in self.movements.all()])
    @property
    def profit(self): return self.total - self.material_cost
    def write_off_materials(self):
        if self.materials_written_off: return
        with transaction.atomic():
            for item in self.items.select_related('service'):
                for norm in item.service.norms.select_related('material'):
                    qty=norm.qty*item.qty
                    mat=norm.material
                    mat.stock=mat.stock-qty
                    mat.save(update_fields=['stock'])
                    StockMovement.objects.create(material=mat, order=self, qty=-qty, unit_cost=mat.cost, comment=f'Списание по {item.service.name}')
            self.materials_written_off=True
            self.save(update_fields=['materials_written_off'])
    def __str__(self): return self.number

class WorkOrderItem(models.Model):
    order=models.ForeignKey(WorkOrder,on_delete=models.CASCADE,related_name='items')
    service=models.ForeignKey(Service,on_delete=models.PROTECT, verbose_name='Услуга')
    qty=models.DecimalField('Кол-во', max_digits=10, decimal_places=2, default=1)
    price=models.DecimalField('Цена', max_digits=12, decimal_places=2)
    line_discount=models.DecimalField('Скидка по строке', max_digits=12, decimal_places=2, default=0)
    comment=models.CharField('Комментарий к работе', max_length=255, blank=True)
    created_at=models.DateTimeField(auto_now_add=True, null=True)
    @property
    def total(self): return max((self.qty*self.price) - self.line_discount, 0)
    def save(self,*args,**kwargs):
        if not self.price and self.service_id: self.price=self.service.price
        super().save(*args,**kwargs)
    def __str__(self):
        return f'{self.order} — {self.service}'

class StockMovement(models.Model):
    material=models.ForeignKey(Material,on_delete=models.PROTECT,related_name='movements')
    order=models.ForeignKey(WorkOrder,on_delete=models.SET_NULL,null=True,blank=True,related_name='movements')
    qty=models.DecimalField('Количество', max_digits=12, decimal_places=3)
    unit_cost=models.DecimalField('Цена ед.', max_digits=12, decimal_places=2, default=0)
    comment=models.CharField('Комментарий', max_length=255, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    @property
    def total_cost(self): return abs(self.qty)*self.unit_cost
    def __str__(self): return f'{self.material} {self.qty}'


class Booking(models.Model):
    STATUS=[('planned','Запланировано'),('arrived','Приехал'),('work','В работе'),('ready','Готово'),('done','Завершено'),('cancel','Отменено')]
    customer=models.ForeignKey(Customer,on_delete=models.PROTECT, verbose_name='Клиент')
    car=models.ForeignKey(Car,on_delete=models.PROTECT, verbose_name='Автомобиль')
    service=models.ForeignKey(Service,on_delete=models.SET_NULL,null=True,blank=True, verbose_name='Услуга')
    start_at=models.DateTimeField('Дата и время записи')
    duration_minutes=models.PositiveIntegerField('Длительность, минут', default=180)
    status=models.CharField('Статус', max_length=20, choices=STATUS, default='planned')
    notes=models.TextField('Комментарий', blank=True)
    order=models.OneToOneField(WorkOrder,on_delete=models.SET_NULL,null=True,blank=True, related_name='booking', verbose_name='Заказ-наряд')
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['start_at']
    def __str__(self):
        return f'{self.start_at:%d.%m.%Y %H:%M} — {self.customer} — {self.car}'
