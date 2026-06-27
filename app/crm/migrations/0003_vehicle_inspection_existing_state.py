import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_workorderitem_line_fields'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='VehicleInspection',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('mileage', models.PositiveIntegerField(blank=True, null=True, verbose_name='Пробег при приеме')),
                        ('fuel_level', models.CharField(blank=True, choices=[('empty', 'Пусто'), ('quarter', '1/4'), ('half', '1/2'), ('three_quarters', '3/4'), ('full', 'Полный')], max_length=20, verbose_name='Уровень топлива')),
                        ('general_comment', models.TextField(blank=True, verbose_name='Комментарий приемщика')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='inspection', to='crm.workorder', verbose_name='Заказ-наряд')),
                    ],
                ),
                migrations.CreateModel(
                    name='VehicleDamage',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('zone', models.CharField(choices=[('front_bumper', 'Передний бампер'), ('hood', 'Капот'), ('roof', 'Крыша'), ('windshield', 'Лобовое стекло'), ('left_fender', 'Левое крыло'), ('left_front_door', 'Левая передняя дверь'), ('left_rear_door', 'Левая задняя дверь'), ('left_rear_fender', 'Левое заднее крыло'), ('right_fender', 'Правое крыло'), ('right_front_door', 'Правая передняя дверь'), ('right_rear_door', 'Правая задняя дверь'), ('right_rear_fender', 'Правое заднее крыло'), ('trunk', 'Крышка багажника'), ('rear_bumper', 'Задний бампер'), ('wheels', 'Диски/колеса'), ('interior', 'Салон'), ('other', 'Другое')], max_length=40, verbose_name='Зона авто')),
                        ('damage_type', models.CharField(choices=[('scratch', 'Царапина'), ('chip', 'Скол'), ('dent', 'Вмятина'), ('crack', 'Трещина'), ('scuff', 'Потертость'), ('stain', 'Пятно'), ('other', 'Другое')], max_length=40, verbose_name='Тип повреждения')),
                        ('comment', models.CharField(blank=True, max_length=255, verbose_name='Комментарий')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('inspection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='damages', to='crm.vehicleinspection', verbose_name='Осмотр')),
                    ],
                ),
                migrations.CreateModel(
                    name='WorkOrderPhoto',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('image', models.ImageField(upload_to='work_orders/%Y/%m/', verbose_name='Фото')),
                        ('photo_type', models.CharField(choices=[('before', 'До'), ('after', 'После')], default='before', max_length=10, verbose_name='Тип фото')),
                        ('comment', models.CharField(blank=True, max_length=255, verbose_name='Комментарий')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='crm.workorder', verbose_name='Заказ-наряд')),
                    ],
                ),
            ],
        ),
    ]
