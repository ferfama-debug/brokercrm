from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0028_policytype_policy_email_15_dias_enviado_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='logo_emoji',
            field=models.CharField(blank=True, default='🏢', help_text='Un emoji simple para identificarla rápido (opcional)', max_length=10, verbose_name='Ícono'),
        ),
        migrations.AddField(
            model_name='company',
            name='notas',
            field=models.CharField(blank=True, help_text="Ej: 'Usuario y clave en el mail de bienvenida'", max_length=255, verbose_name='Notas'),
        ),
        migrations.AddField(
            model_name='company',
            name='telefono',
            field=models.CharField(blank=True, help_text='Opcional', max_length=50, verbose_name='Teléfono'),
        ),
        migrations.AddField(
            model_name='company',
            name='url_portal',
            field=models.URLField(blank=True, help_text='Ej: https://www.aseguradora.com/siniestros', verbose_name='Link al portal'),
        ),
    ]
