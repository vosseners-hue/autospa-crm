from django import forms
from django.forms import inlineformset_factory
from .models import Customer, Car, Service, Material, StockMovement, WorkOrder, WorkOrderItem, Booking

class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

class CustomerForm(StyledModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'messenger', 'source', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 4})}

class CustomerWithCarForm(CustomerForm):
    car_brand = forms.CharField(label='Марка авто', required=False, max_length=80, widget=forms.Select(attrs={'data-car-brand': '1'}))
    car_model = forms.CharField(label='Модель авто', required=False, max_length=80, widget=forms.Select(attrs={'data-car-model': '1'}))
    car_year = forms.IntegerField(label='Год', required=False, min_value=1900, max_value=2100)
    car_plate = forms.CharField(label='Госномер', required=False, max_length=40)
    car_vin = forms.CharField(label='VIN', required=False, max_length=40)
    car_color = forms.CharField(label='Цвет', required=False, max_length=80, widget=forms.Select(attrs={'data-car-color': '1'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    class Meta(CustomerForm.Meta):
        fields = ['name', 'phone', 'messenger', 'source', 'notes', 'car_brand', 'car_model', 'car_year', 'car_plate', 'car_vin', 'car_color']

    def clean(self):
        cleaned = super().clean()
        car_values = [cleaned.get('car_brand'), cleaned.get('car_model'), cleaned.get('car_year'), cleaned.get('car_plate'), cleaned.get('car_vin'), cleaned.get('car_color')]
        if any(car_values) and not cleaned.get('car_brand'):
            self.add_error('car_brand', 'Укажите марку автомобиля или оставьте все поля авто пустыми.')
        if any(car_values) and not cleaned.get('car_model'):
            self.add_error('car_model', 'Укажите модель автомобиля или оставьте все поля авто пустыми.')
        return cleaned

    def save(self, commit=True):
        customer = super().save(commit=commit)
        car_values = [self.cleaned_data.get('car_brand'), self.cleaned_data.get('car_model'), self.cleaned_data.get('car_year'), self.cleaned_data.get('car_plate'), self.cleaned_data.get('car_vin'), self.cleaned_data.get('car_color')]
        if commit and any(car_values):
            Car.objects.create(
                customer=customer,
                brand=self.cleaned_data.get('car_brand') or '',
                model=self.cleaned_data.get('car_model') or '',
                year=self.cleaned_data.get('car_year'),
                plate=self.cleaned_data.get('car_plate') or '',
                vin=self.cleaned_data.get('car_vin') or '',
                color=self.cleaned_data.get('car_color') or '',
            )
        return customer

class CarForm(StyledModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].label = 'Владелец / клиент'
        self.fields['customer'].queryset = Customer.objects.order_by('name')
        self.fields['brand'].widget = forms.Select(attrs={'class': 'form-control', 'data-car-brand': '1'})
        self.fields['model'].widget = forms.Select(attrs={'class': 'form-control', 'data-car-model': '1'})
        self.fields['color'].widget = forms.Select(attrs={'class': 'form-control', 'data-car-color': '1'})

    class Meta:
        model = Car
        fields = ['customer', 'brand', 'model', 'year', 'plate', 'vin', 'color']

class ServiceForm(StyledModelForm):
    class Meta:
        model = Service
        fields = ['name', 'price', 'description', 'active']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

class MaterialForm(StyledModelForm):
    class Meta:
        model = Material
        fields = ['name', 'unit', 'stock', 'cost', 'min_stock']

class StockMovementForm(StyledModelForm):
    class Meta:
        model = StockMovement
        fields = ['material', 'qty', 'unit_cost', 'comment']
        help_texts = {'qty': 'Для прихода укажите положительное число, для списания — отрицательное.'}


class BookingForm(StyledModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.order_by('name')
        self.fields['car'].queryset = Car.objects.select_related('customer').order_by('brand', 'model', 'plate')
        self.fields['service'].queryset = Service.objects.filter(active=True).order_by('name')
        self.fields['customer'].label = 'Клиент'
        self.fields['car'].label = 'Автомобиль клиента'

    class Meta:
        model = Booking
        fields = ['customer', 'car', 'service', 'start_at', 'duration_minutes', 'status', 'notes']
        widgets = {
            'start_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

class WorkOrderForm(StyledModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.order_by('name')
        self.fields['car'].queryset = Car.objects.select_related('customer').order_by('brand', 'model', 'plate')
        self.fields['customer'].label = 'Клиент'
        self.fields['car'].label = 'Автомобиль клиента'

    class Meta:
        model = WorkOrder
        fields = ['customer', 'car', 'status', 'planned_out', 'discount', 'notes']
        widgets = {
            'planned_out': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

class WorkOrderItemForm(StyledModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price'].required = False

    class Meta:
        model = WorkOrderItem
        fields = ['service', 'qty', 'price', 'line_discount', 'comment']

    def clean_price(self):
        price = self.cleaned_data.get('price')
        service = self.cleaned_data.get('service')
        if (price is None or price == 0) and service:
            return service.price
        return price

WorkOrderItemFormSet = inlineformset_factory(
    WorkOrder,
    WorkOrderItem,
    form=WorkOrderItemForm,
    extra=3,
    can_delete=True,
    fields=['service', 'qty', 'price', 'line_discount', 'comment'],
)
