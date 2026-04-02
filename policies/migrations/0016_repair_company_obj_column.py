from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("policies", "0015_alter_policy_company_alter_policy_company_obj"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE policies_policy
            ADD COLUMN IF NOT EXISTS company_obj_id bigint NULL;
            """,
            reverse_sql="""
            ALTER TABLE policies_policy
            DROP COLUMN IF EXISTS company_obj_id;
            """,
        ),
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS policies_policy_company_obj_id_idx
            ON policies_policy (company_obj_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS policies_policy_company_obj_id_idx;
            """,
        ),
    ]