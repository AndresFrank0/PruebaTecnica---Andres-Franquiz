# Generada por Django 5.2.17 el 2026-09-27 14:09

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('author', models.CharField(max_length=255)),
                ('isbn', models.CharField(max_length=13, unique=True, validators=[django.core.validators.RegexValidator('^([0-9]{9}[0-9X]|[0-9]{13})\\Z', 'El ISBN debe tener 10 o 13 dígitos.')])),
                ('cost_usd', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('selling_price_local', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('stock_quantity', models.PositiveIntegerField(default=0)),
                ('category', models.CharField(max_length=100)),
                ('supplier_country', models.CharField(max_length=2, validators=[django.core.validators.RegexValidator('^[A-Z]{2}$', 'Debe ser un código de país ISO de 2 letras (ej. ES).')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'libro',
                'ordering': ['id'],
            },
        ),
    ]
