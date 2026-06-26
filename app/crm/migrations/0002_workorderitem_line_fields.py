# Generated for Auto Spa CRM WorkOrderItem foundation

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorderitem',
            name='line_discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Скидка по строке'),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='comment',
            field=models.CharField(blank=True, max_length=255, verbose_name='Комментарий к работе'),
        ),
        migrations.AddField(
            model_name='workorderitem',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
