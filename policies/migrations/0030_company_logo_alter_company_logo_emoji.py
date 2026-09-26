from django.db import migrations, models
import policies.models


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0029_company_logo_emoji_company_notas_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='logo_emoji',
            field=models.CharField(blank=True, default='🏢', help_text='Se usa solo si no subiste una imagen de logo', max_length=10, verbose_name='Ícono (si no hay logo)'),
        ),
        migrations.AddField(
            model_name='company',
            name='logo',
            field=models.ImageField(blank=True, help_text='Subí el logo en PNG o JPG, se muestra en vez del ícono', max_length=500, null=True, storage=policies.models.SupabaseBypassStorage(), upload_to=policies.models.company_logo_directory_path, verbose_name='Logo (imagen)'),
        ),
    ]
