# Generated by Django 4.2.3 on 2024-07-12 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0002_kyc'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashaccount',
            name='customer_id',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='kyc',
            name='customer_id',
            field=models.TextField(null=True),
        ),
    ]
