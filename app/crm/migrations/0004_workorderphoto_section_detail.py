from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_vehicle_inspection_existing_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorderphoto',
            name='section',
            field=models.CharField(blank=True, choices=[('exterior', 'Экстерьер'), ('interior', 'Интерьер')], max_length=20, verbose_name='Раздел'),
        ),
        migrations.AddField(
            model_name='workorderphoto',
            name='detail',
            field=models.CharField(blank=True, choices=[('front_bumper', 'Передний бампер'), ('hood', 'Капот'), ('front_left_fender', 'Переднее левое крыло'), ('front_right_fender', 'Переднее правое крыло'), ('left_front_door', 'Левая передняя дверь'), ('left_rear_door', 'Левая задняя дверь'), ('right_front_door', 'Правая передняя дверь'), ('right_rear_door', 'Правая задняя дверь'), ('roof', 'Крыша'), ('trunk', 'Багажник'), ('rear_bumper', 'Задний бампер'), ('wheels', 'Диски/колеса'), ('glass', 'Стекла'), ('other', 'Другое'), ('front_seats', 'Передние сиденья'), ('rear_seats', 'Задние сиденья'), ('dashboard', 'Торпедо'), ('steering_wheel', 'Руль'), ('door_cards', 'Карты дверей'), ('floor', 'Пол/ковры'), ('ceiling', 'Потолок'), ('trunk_interior', 'Багажное отделение'), ('other', 'Другое')], max_length=40, verbose_name='Деталь'),
        ),
    ]
