from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.utils.safestring import mark_safe
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from .models import *
from .forms import CustomerForm, CustomerWithCarForm, CarForm, ServiceForm, MaterialForm, StockMovementForm, WorkOrderForm, WorkOrderItemFormSet, BookingForm, VehicleInspectionForm, VehicleDamageForm, WorkOrderPhotoForm, ServiceMaterialForm


def _money(value):
    return value or 0


@login_required
def reception(request):
    q = (request.GET.get('q') or '').strip()
    customers_qs = Customer.objects.prefetch_related('cars').order_by('-created_at')
    cars_qs = Car.objects.select_related('customer').order_by('brand', 'model', 'plate')
    if q:
        customers_qs = customers_qs.filter(
            Q(name__icontains=q) | Q(phone__icontains=q) | Q(messenger__icontains=q) | Q(notes__icontains=q)
        )
        cars_qs = cars_qs.filter(
            Q(brand__icontains=q) | Q(model__icontains=q) | Q(plate__icontains=q) | Q(vin__icontains=q) | Q(color__icontains=q) | Q(customer__name__icontains=q) | Q(customer__phone__icontains=q)
        )
    recent_orders = WorkOrder.objects.select_related('customer', 'car').prefetch_related('items__service').order_by('-date_in')[:8]
    return render(request, 'crm/reception.html', {
        'q': q,
        'customers': customers_qs[:12],
        'cars': cars_qs[:18],
        'recent_orders': recent_orders,
        'services': Service.objects.filter(active=True).order_by('name')[:12],
    })



@login_required
def reception_create_order(request):
    if request.method != 'POST':
        return redirect('reception')

    car_id = request.POST.get('car')
    service_id = request.POST.get('service')
    notes = (request.POST.get('notes') or '').strip()

    if not car_id:
        messages.error(request, 'Выберите автомобиль для создания заказ-наряда')
        return redirect('reception')

    car = get_object_or_404(Car.objects.select_related('customer'), pk=car_id)
    order = WorkOrder.objects.create(
        customer=car.customer,
        car=car,
        notes=notes,
    )

    if service_id:
        service = get_object_or_404(Service, pk=service_id)
        WorkOrderItem.objects.create(
            order=order,
            service=service,
            qty=1,
            price=service.price,
        )

    messages.success(request, f'Заказ-наряд {order.number} создан из экрана приема')
    return redirect('order_detail', pk=order.pk)


@login_required
def booking(request):
    day = (request.GET.get('day') or '').strip()
    bookings_qs = Booking.objects.select_related('customer', 'car', 'service', 'order').order_by('start_at')
    if day:
        bookings_qs = bookings_qs.filter(start_at__date=day)
    else:
        bookings_qs = bookings_qs.order_by('start_at')[:80]
    return render(request, 'crm/booking.html', {
        'bookings': bookings_qs,
        'day': day,
        'customers': Customer.objects.order_by('name'),
        'cars_json': _cars_for_order_json(),
    })

@login_required
def booking_create(request):
    instance = Booking()
    customer_id = request.GET.get('customer')
    car_id = request.GET.get('car')
    if customer_id:
        try:
            instance.customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            pass
    if car_id:
        try:
            instance.car = Car.objects.get(pk=car_id)
            instance.customer = instance.car.customer
        except Car.DoesNotExist:
            pass
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=instance)
        if form.is_valid():
            booking_obj = form.save()
            messages.success(request, 'Запись создана')
            return redirect('booking')
    else:
        form = BookingForm(instance=instance)
    return render(request, 'crm/booking_form.html', {
        'form': form,
        'title': 'Новая запись',
        'back_url': 'booking',
        'submit_label': 'Сохранить запись',
        'cars_json': _cars_for_order_json(),
    })

@login_required
def booking_update(request, pk):
    booking_obj = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Запись обновлена')
            return redirect('booking')
    else:
        form = BookingForm(instance=booking_obj)
    return render(request, 'crm/booking_form.html', {
        'form': form,
        'title': 'Редактирование записи',
        'back_url': 'booking',
        'submit_label': 'Сохранить запись',
        'cars_json': _cars_for_order_json(),
    })

@login_required
def booking_delete(request, pk):
    return _delete_view(request, get_object_or_404(Booking, pk=pk), 'booking')

@login_required
def booking_create_order(request, pk):
    booking_obj = get_object_or_404(Booking.objects.select_related('customer', 'car', 'service'), pk=pk)
    if booking_obj.order_id:
        return redirect('order_detail', pk=booking_obj.order_id)
    order = WorkOrder.objects.create(
        customer=booking_obj.customer,
        car=booking_obj.car,
        planned_out=booking_obj.start_at,
        notes=booking_obj.notes,
    )
    if booking_obj.service_id:
        WorkOrderItem.objects.create(order=order, service=booking_obj.service, qty=1, price=booking_obj.service.price)
    booking_obj.order = order
    booking_obj.status = 'arrived'
    booking_obj.save(update_fields=['order', 'status'])
    messages.success(request, f'Создан заказ-наряд {order.number} из записи')
    return redirect('order_detail', pk=order.pk)

@login_required
def dashboard(request):
    today = timezone.localdate()
    today_orders_qs = WorkOrder.objects.filter(date_in__date=today).select_related('customer', 'car').prefetch_related('items__service')
    active_orders_qs = WorkOrder.objects.exclude(status__in=['done', 'cancel']).select_related('customer', 'car')
    ready_orders_qs = WorkOrder.objects.filter(status='ready').select_related('customer', 'car')
    done_today_qs = WorkOrder.objects.filter(status='done', date_in__date=today).prefetch_related('items')
    upcoming_bookings_qs = Booking.objects.filter(start_at__date=today).select_related('customer', 'car', 'service', 'order').order_by('start_at')
    low_materials = [m for m in Material.objects.all().order_by('name') if m.stock <= m.min_stock]

    return render(request, 'crm/dashboard.html', {
        'today': today,
        'orders_count': WorkOrder.objects.count(),
        'customers_count': Customer.objects.count(),
        'cars_count': Car.objects.count(),
        'materials_count': Material.objects.count(),
        'today_orders_count': today_orders_qs.count(),
        'active_orders': active_orders_qs.count(),
        'ready_orders': ready_orders_qs.count(),
        'revenue_today': sum([o.total for o in done_today_qs]),
        'revenue_total': sum([o.total for o in WorkOrder.objects.filter(status='done')]),
        'average_check_today': (sum([o.total for o in done_today_qs]) / done_today_qs.count()) if done_today_qs.count() else 0,
        'recent_orders': WorkOrder.objects.select_related('customer', 'car').prefetch_related('items__service').order_by('-date_in')[:8],
        'today_orders': today_orders_qs.order_by('-date_in')[:8],
        'today_bookings': upcoming_bookings_qs[:8],
        'low_materials': low_materials[:8],
        'low_materials_count': len(low_materials),
    })

@login_required
def customers(request):
    return render(request, 'crm/customers.html', {'customers': Customer.objects.prefetch_related('cars').order_by('-created_at')})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer.objects.prefetch_related('cars'), pk=pk)
    orders_qs = WorkOrder.objects.filter(customer=customer).select_related('car').prefetch_related('items__service').order_by('-date_in')
    cars_qs = customer.cars.all().order_by('brand', 'model', 'plate')
    total_sum = sum([o.total for o in orders_qs])
    done_sum = sum([o.total for o in orders_qs if o.status == 'done'])
    active_orders = orders_qs.exclude(status__in=['done', 'cancel']).count()
    return render(request, 'crm/customer_detail.html', {
        'customer': customer,
        'cars': cars_qs,
        'orders': orders_qs,
        'orders_count': orders_qs.count(),
        'total_sum': total_sum,
        'done_sum': done_sum,
        'active_orders': active_orders,
    })

@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerWithCarForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Клиент и автомобиль сохранены')
            return redirect('customers')
    else:
        form = CustomerWithCarForm()
    return render(request, 'crm/customer_form.html', {'form': form, 'title': 'Новый клиент', 'back_url': 'customers', 'submit_label': 'Сохранить клиента'})

@login_required
def customer_update(request, pk):
    return _model_form(request, CustomerForm, 'Клиент', 'customers', get_object_or_404(Customer, pk=pk))

@login_required
def customer_delete(request, pk):
    return _delete_view(request, get_object_or_404(Customer, pk=pk), 'customers')

@login_required
def cars(request):
    return render(request, 'crm/cars.html', {'cars': Car.objects.select_related('customer').order_by('brand', 'model')})


@login_required
def car_detail(request, pk):
    car = get_object_or_404(Car.objects.select_related('customer'), pk=pk)
    orders_qs = WorkOrder.objects.filter(car=car).select_related('customer').prefetch_related('items__service').order_by('-date_in')
    total_sum = sum([o.total for o in orders_qs])
    done_sum = sum([o.total for o in orders_qs if o.status == 'done'])
    active_orders = orders_qs.exclude(status__in=['done', 'cancel']).count()
    last_order = orders_qs.first()
    return render(request, 'crm/car_detail.html', {
        'car': car,
        'customer': car.customer,
        'orders': orders_qs,
        'orders_count': orders_qs.count(),
        'total_sum': total_sum,
        'done_sum': done_sum,
        'active_orders': active_orders,
        'last_order': last_order,
    })

@login_required
def car_create(request):
    instance = None
    customer_id = request.GET.get('customer')
    if customer_id:
        customer = get_object_or_404(Customer, pk=customer_id)
        instance = Car(customer=customer)
    return _model_form(request, CarForm, 'Автомобиль', 'cars', instance)

@login_required
def car_update(request, pk):
    return _model_form(request, CarForm, 'Автомобиль', 'cars', get_object_or_404(Car, pk=pk))

@login_required
def car_delete(request, pk):
    return _delete_view(request, get_object_or_404(Car, pk=pk), 'cars')

@login_required
def services(request):
    return render(request, 'crm/services.html', {'services': Service.objects.prefetch_related('norms').order_by('name')})

@login_required
def service_create(request):
    return _model_form(request, ServiceForm, 'Услуга', 'services')

@login_required
def service_update(request, pk):
    return _model_form(request, ServiceForm, 'Услуга', 'services', get_object_or_404(Service, pk=pk))

@login_required
def service_delete(request, pk):
    return _delete_view(request, get_object_or_404(Service, pk=pk), 'services')

@login_required
def service_materials(request, pk):
    service = get_object_or_404(Service.objects.prefetch_related('norms__material'), pk=pk)
    norms = service.norms.select_related('material').order_by('material__name')
    return render(request, 'crm/service_materials.html', {
        'service': service,
        'norms': norms,
    })

@login_required
def service_material_create(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceMaterialForm(request.POST, service=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Материал привязан к услуге')
            return redirect('service_materials', pk=service.pk)
    else:
        form = ServiceMaterialForm(service=service)
    return render(request, 'crm/service_material_form.html', {
        'form': form,
        'service': service,
        'title': 'Добавить материал к услуге',
        'submit_label': 'Сохранить материал',
    })

@login_required
def service_material_update(request, pk, norm_id):
    service = get_object_or_404(Service, pk=pk)
    norm = get_object_or_404(ServiceMaterial, pk=norm_id, service=service)
    if request.method == 'POST':
        form = ServiceMaterialForm(request.POST, instance=norm, service=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Норма расхода обновлена')
            return redirect('service_materials', pk=service.pk)
    else:
        form = ServiceMaterialForm(instance=norm, service=service)
    return render(request, 'crm/service_material_form.html', {
        'form': form,
        'service': service,
        'norm': norm,
        'title': 'Редактировать материал услуги',
        'submit_label': 'Сохранить изменения',
    })

@login_required
def service_material_delete(request, pk, norm_id):
    service = get_object_or_404(Service, pk=pk)
    norm = get_object_or_404(ServiceMaterial, pk=norm_id, service=service)
    if request.method == 'POST':
        norm.delete()
        messages.success(request, 'Материал отвязан от услуги')
    return redirect('service_materials', pk=service.pk)

@login_required
def inventory(request):
    return render(request, 'crm/inventory.html', {'materials': Material.objects.order_by('name')})

@login_required
def material_create(request):
    return _model_form(request, MaterialForm, 'Материал', 'inventory')

@login_required
def material_update(request, pk):
    return _model_form(request, MaterialForm, 'Материал', 'inventory', get_object_or_404(Material, pk=pk))

@login_required
def material_delete(request, pk):
    return _delete_view(request, get_object_or_404(Material, pk=pk), 'inventory')

@login_required
def stock_movements(request):
    return render(request, 'crm/stock_movements.html', {'movements': StockMovement.objects.select_related('material', 'order').order_by('-created_at')[:200]})

@login_required
def stock_movement_create(request):
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save()
            material = movement.material
            material.stock = material.stock + movement.qty
            material.save(update_fields=['stock'])
            messages.success(request, 'Движение склада добавлено, остаток обновлен')
            return redirect('stock_movements')
    else:
        form = StockMovementForm()
    return render(request, 'crm/form.html', {'form': form, 'title': 'Движение склада', 'back_url': 'stock_movements', 'submit_label': 'Сохранить движение'})

@login_required
def orders(request):
    return render(request, 'crm/orders.html', {'orders': WorkOrder.objects.select_related('customer', 'car').order_by('-date_in')})


def _cars_for_order_json():
    data = [
        {
            'id': car.id,
            'customer_id': car.customer_id,
            'title': f'{car.brand} {car.model} — {car.plate or "без номера"}',
        }
        for car in Car.objects.select_related('customer').order_by('brand', 'model', 'plate')
    ]
    return mark_safe(json.dumps(data, ensure_ascii=False))


def _services_for_order_json():
    data = []
    for service in Service.objects.filter(active=True).prefetch_related('norms__material').order_by('name'):
        data.append({
            'id': service.id,
            'name': service.name,
            'price': float(service.price or 0),
            'norms': [
                {
                    'material': norm.material.name,
                    'qty': float(norm.qty or 0),
                    'unit': norm.material.get_unit_display(),
                    'cost': float(norm.material.cost or 0),
                }
                for norm in service.norms.all()
            ],
        })
    return mark_safe(json.dumps(data, ensure_ascii=False))

@login_required
def order_create(request):
    order = WorkOrder()
    customer_id = request.GET.get('customer')
    car_id = request.GET.get('car')
    if customer_id:
        try:
            order.customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            pass
    if car_id:
        try:
            order.car = Car.objects.get(pk=car_id)
            order.customer = order.car.customer
        except Car.DoesNotExist:
            pass
    if request.method == 'POST':
        form = WorkOrderForm(request.POST, instance=order)
        formset = WorkOrderItemFormSet(request.POST, instance=order)
        form_ok = form.is_valid()
        formset_ok = formset.is_valid()

        if form_ok and formset_ok:
            order = form.save()
            formset.instance = order
            formset.save()
            messages.success(request, 'Заказ-наряд создан')
            return redirect('order_detail', pk=order.pk)
        else:
            messages.error(request, 'Заказ-наряд не сохранен. Проверьте ошибки ниже.')
            for field, errors in form.errors.items():
                messages.error(request, f'Поле {field}: {errors}')
            for error in form.non_field_errors():
                messages.error(request, f'Ошибка формы: {error}')
            for idx, item_form in enumerate(formset.forms, start=1):
                if item_form.errors:
                    messages.error(request, f'Строка услуги {idx}: {item_form.errors}')
            for error in formset.non_form_errors():
                messages.error(request, f'Ошибка услуг: {error}')
    else:
        form = WorkOrderForm(instance=order)
        formset = WorkOrderItemFormSet(instance=order)
    return render(request, 'crm/order_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Новый заказ-наряд',
        'cars_json': _cars_for_order_json(),
        'services_json': _services_for_order_json(),
    })

@login_required
def order_update(request, pk):
    order = get_object_or_404(WorkOrder, pk=pk)
    if request.method == 'POST':
        form = WorkOrderForm(request.POST, instance=order)
        formset = WorkOrderItemFormSet(request.POST, instance=order)
        form_ok = form.is_valid()
        formset_ok = formset.is_valid()

        if form_ok and formset_ok:
            order = form.save()
            formset.save()
            if order.status == 'done' and not order.materials_written_off:
                order.write_off_materials()
            messages.success(request, 'Заказ-наряд обновлен')
            return redirect('order_detail', pk=order.pk)
        else:
            messages.error(request, 'Заказ-наряд не сохранен. Проверьте ошибки ниже.')
            for field, errors in form.errors.items():
                messages.error(request, f'Поле {field}: {errors}')
            for error in form.non_field_errors():
                messages.error(request, f'Ошибка формы: {error}')
            for idx, item_form in enumerate(formset.forms, start=1):
                if item_form.errors:
                    messages.error(request, f'Строка услуги {idx}: {item_form.errors}')
            for error in formset.non_form_errors():
                messages.error(request, f'Ошибка услуг: {error}')
    else:
        form = WorkOrderForm(instance=order)
        formset = WorkOrderItemFormSet(instance=order)
    return render(request, 'crm/order_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Редактирование {order.number}',
        'order': order,
        'cars_json': _cars_for_order_json(),
        'services_json': _services_for_order_json(),
    })

@login_required
def order_delete(request, pk):
    return _delete_view(request, get_object_or_404(WorkOrder, pk=pk), 'orders')

@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        WorkOrder.objects.select_related('customer', 'car').prefetch_related('items__service', 'photos'),
        pk=pk
    )
    inspection = getattr(order, 'inspection', None)
    return render(request, 'crm/order_detail.html', {'order': order, 'inspection': inspection})

@login_required
def order_inspection(request, pk):
    order = get_object_or_404(WorkOrder.objects.select_related('customer', 'car'), pk=pk)
    inspection, created = VehicleInspection.objects.get_or_create(order=order)
    damage_form = VehicleDamageForm(prefix='damage')
    photo_form = WorkOrderPhotoForm(prefix='photo')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_inspection':
            form = VehicleInspectionForm(request.POST, instance=inspection)
            if form.is_valid():
                form.save()
                messages.success(request, 'Осмотр автомобиля сохранен')
                return redirect('order_inspection', pk=order.pk)
        elif action == 'add_damage':
            form = VehicleInspectionForm(instance=inspection)
            damage_form = VehicleDamageForm(request.POST, prefix='damage')
            if damage_form.is_valid():
                damage = damage_form.save(commit=False)
                damage.inspection = inspection
                damage.save()
                messages.success(request, 'Повреждение добавлено')
                return redirect('order_inspection', pk=order.pk)
        elif action == 'add_photo':
            form = VehicleInspectionForm(instance=inspection)
            photo_form = WorkOrderPhotoForm(request.POST, request.FILES, prefix='photo')
            if photo_form.is_valid():
                photo = photo_form.save(commit=False)
                photo.order = order
                photo.save()
                messages.success(request, 'Фото добавлено')
                return redirect('order_inspection', pk=order.pk)
        else:
            form = VehicleInspectionForm(instance=inspection)
    else:
        form = VehicleInspectionForm(instance=inspection)

    return render(request, 'crm/order_inspection.html', {
        'order': order,
        'inspection': inspection,
        'form': form,
        'damage_form': damage_form,
        'photo_form': photo_form,
        'damages': inspection.damages.all().order_by('-created_at'),
        'photos': order.photos.all().order_by('-created_at'),
        'photos_before': order.photos.filter(photo_type='before').order_by('-created_at'),
        'photos_after': order.photos.filter(photo_type='after').order_by('-created_at'),
    })

@login_required
def order_damage_delete(request, pk, damage_id):
    order = get_object_or_404(WorkOrder, pk=pk)
    damage = get_object_or_404(VehicleDamage, pk=damage_id, inspection__order=order)
    damage.delete()
    messages.success(request, 'Повреждение удалено')
    return redirect('order_inspection', pk=order.pk)

@login_required
def order_photo_delete(request, pk, photo_id):
    order = get_object_or_404(WorkOrder, pk=pk)
    photo = get_object_or_404(WorkOrderPhoto, pk=photo_id, order=order)
    photo.delete()
    messages.success(request, 'Фото удалено')
    return redirect('order_inspection', pk=order.pk)

@login_required
def order_writeoff(request, pk):
    order = get_object_or_404(WorkOrder, pk=pk)
    order.write_off_materials()
    messages.success(request, 'Материалы списаны со склада')
    return redirect('order_detail', pk=pk)

@login_required
def order_close(request, pk):
    order = get_object_or_404(WorkOrder, pk=pk)
    order.status = 'done'
    order.save(update_fields=['status'])
    if not order.materials_written_off:
        order.write_off_materials()
    messages.success(request, 'Авто выдано, материалы списаны')
    return redirect('order_detail', pk=pk)

@login_required
def order_print(request, pk):
    return render(request, 'crm/order_print.html', {'order': get_object_or_404(WorkOrder, pk=pk)})

@login_required
def order_pdf(request, pk):
    order = get_object_or_404(WorkOrder, pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{order.number}.pdf"'
    p = canvas.Canvas(response, pagesize=A4); w, h = A4
    p.setFont('Helvetica-Bold', 18); p.drawString(20*mm, h-25*mm, 'AUTO SPA DETAILING - WORK ORDER')
    p.setFont('Helvetica', 11)
    y = h - 40*mm
    rows = [f'Order: {order.number}', f'Client: {order.customer.name} / {order.customer.phone}', f'Car: {order.car.brand} {order.car.model} {order.car.plate}', f'Status: {order.get_status_display()}']
    for r in rows:
        p.drawString(20*mm, y, r); y -= 8*mm
    y -= 5*mm; p.setFont('Helvetica-Bold', 12); p.drawString(20*mm, y, 'Services'); y -= 8*mm; p.setFont('Helvetica', 10)
    for i in order.items.select_related('service'):
        p.drawString(20*mm, y, f'{i.service.name} x {i.qty} = {i.total} RUB'); y -= 7*mm
    y -= 5*mm; p.setFont('Helvetica-Bold', 12); p.drawString(20*mm, y, f'Total: {order.total} RUB')
    y -= 15*mm; p.setFont('Helvetica', 10); p.drawString(20*mm, y, 'Client signature: ____________________')
    p.showPage(); p.save(); return response


def _model_form(request, form_class, object_title, success_url_name, instance=None):
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'{object_title} сохранен')
            return redirect(success_url_name)
    else:
        form = form_class(instance=instance)
    title = f'{"Новый" if instance is None else "Редактирование"} {object_title.lower()}'
    return render(request, 'crm/form.html', {'form': form, 'title': title, 'back_url': success_url_name, 'submit_label': 'Сохранить'})


def _delete_view(request, obj, success_url_name):
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Запись удалена')
        return redirect(success_url_name)
    return render(request, 'crm/confirm_delete.html', {'object': obj, 'back_url': success_url_name})
