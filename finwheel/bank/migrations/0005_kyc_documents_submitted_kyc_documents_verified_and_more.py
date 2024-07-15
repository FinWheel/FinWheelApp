# Generated by Django 4.2.3 on 2024-07-14 22:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0004_kyc_for_user_kyc_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='kyc',
            name='documents_submitted',
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name='kyc',
            name='documents_verified',
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name='kyc',
            name='needs_documents',
            field=models.BooleanField(null=True),
        ),
    ]