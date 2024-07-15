# Generated by Django 4.2.3 on 2024-07-14 23:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bank', '0006_alter_cashaccount_bank_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='externalbankaccount',
            name='for_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='customerexternalaccount', to=settings.AUTH_USER_MODEL),
        ),
    ]
