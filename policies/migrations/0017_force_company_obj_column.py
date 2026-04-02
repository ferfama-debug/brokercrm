from django.db import migrations


class Migration(migrations.Migration):

    from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ("policies", "0015_alter_policy_company_alter_policy_company_obj"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name='policies_policy'
                    AND column_name='company_obj_id'
                ) THEN
                    ALTER TABLE policies_policy
                    ADD COLUMN company_obj_id bigint NULL;
                END IF;
            END$$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]