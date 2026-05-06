from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "policies",
            "0020_alter_emaillog_options_policy_ulti...",
        ),  # He abreviado el nombre, pero usá el nombre EXACTO de tu archivo 0020 (sin el .py)
    ]

    operations = [
        migrations.AddField(
            model_name="policy",
            name="ultimo_envio_cuponera",
            field=models.DateField(
                blank=True, null=True, verbose_name="Última Cuponera Enviada"
            ),
        ),
        migrations.AddField(
            model_name="policy",
            name="ultimo_envio_vencimiento",
            field=models.DateField(
                blank=True, null=True, verbose_name="Último Aviso Vencimiento"
            ),
        ),
    ]
