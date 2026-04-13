from django.db import migrations, connection


def add_company_obj_column_if_needed(apps, schema_editor):
    if connection.vendor != "postgresql":
        return

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'policies_policy'
                    AND column_name = 'company_obj_id'
                ) THEN
                    ALTER TABLE policies_policy
                    ADD COLUMN company_obj_id bigint NULL;
                END IF;
            END$$;
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("policies", "0015_alter_policy_company_alter_policy_company_obj"),
    ]

    operations = [
        migrations.RunPython(
            add_company_obj_column_if_needed,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
