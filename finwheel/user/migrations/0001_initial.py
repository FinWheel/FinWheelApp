# Generated by Django 5.0.2 on 2024-06-29 18:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FinancialPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recurring_deposit_amount', models.DecimalField(decimal_places=2, max_digits=9)),
                ('recurring_deposit_frequency', models.CharField(choices=[('DAY', 'Daily'), ('WEEK', 'Weekly'), ('MONTH', 'Month')], default=None, max_length=5, null=True)),
                ('last_recurring_deposit', models.DateTimeField(null=True)),
                ('next_recurring_deposit', models.DateTimeField(null=True)),
                ('for_user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='UsersPlan', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
