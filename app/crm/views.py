from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from .models import *
from .forms import CustomerForm, CustomerWithCarForm, CarForm, ServiceForm, MaterialForm, StockMovementForm, WorkOrderForm, WorkOrderItemFormSet


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
def dashboard(request):
    return render(request, 'crm/dashboard.html', {
        'orders_count': WorkOrder.objects.count(),
        'customers_count': Customer.objects.count(),
        'cars_count': Car.objects.count(),
        'materials_count': Material.objects.count(),
        'active_orders': WorkOrder.objects.exclude(status__in=['done', 'cancel']).count(),
        'revenue': sum([o.total for o in WorkOrder.objects.filter(status='done')]),
        'orders': WorkOrder.objects.select_related('customer', 'car').order_by('-date_in')[:10],
        'low_materials': [m for m in Material.objects.all() if m.stock <= m.min_stock],
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
    return [
        {
            'id': car.id,
            'customer_id': car.customer_id,
            'title': f'{car.brand} {car.model} — {car.plate or "без номера"}',
        }
        for car in Car.objects.select_related('customer').order_by('brand', 'model', 'plate')
    ]

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
        if form.is_valid() and formset.is_valid():
            order = form.save()
            formset.instance = order
            formset.save()
            messages.success(request, 'Заказ-наряд создан')
            return redirect('order_detail', pk=order.pk)
    else:
        form = WorkOrderForm(instance=order)
        formset = WorkOrderItemFormSet(instance=order)
    return render(request, 'crm/order_form.html', {'form': form, 'formset': formset, 'title': 'Новый заказ-наряд', 'cars_json': _cars_for_order_json()})

@login_required
def order_update(request, pk):
    order = get_object_or_404(WorkOrder, pk=pk)
    if request.method == 'POST':
        form = WorkOrderForm(request.POST, instance=order)
        formset = WorkOrderItemFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            order = form.save()
            formset.save()
            if order.status == 'done' and not order.materials_written_off:
                order.write_off_materials()
            messages.success(request, 'Заказ-наряд обновлен')
            return redirect('order_detail', pk=order.pk)
    else:
        form = WorkOrderForm(instance=order)
        formset = WorkOrderItemFormSet(instance=order)
    return render(request, 'crm/order_form.html', {'form': form, 'formset': formset, 'title': f'Редактирование {order.number}', 'order': order, 'cars_json': _cars_for_order_json()})

@login_required
def order_delete(request, pk):
    return _delete_view(request, get_object_or_404(WorkOrder, pk=pk), 'orders')

@login_required
def order_detail(request, pk):
    return render(request, 'crm/order_detail.html', {'order': get_object_or_404(WorkOrder, pk=pk)})

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
