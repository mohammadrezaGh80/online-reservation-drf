# Generated by Django 5.0.6 on 2024-07-27 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('online_reservation', '0008_alter_specialty_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserve',
            name='zarinpal_authority',
            field=models.CharField(blank=True, max_length=255, verbose_name='Zarinpal authority'),
        ),
        migrations.AddField(
            model_name='reserve',
            name='zarinpal_ref_id',
            field=models.CharField(blank=True, max_length=255, verbose_name='Zarinpal ref_id'),
        ),
    ]
