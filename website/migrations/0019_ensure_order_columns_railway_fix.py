# Emergency fix: ensures order_type, payment_method, table_number columns
# exist in website_order table on Railway PostgreSQL.
# Uses IF NOT EXISTS so safe to run regardless of DB state.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0018_order_order_type_order_payment_method_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE website_order
                    ADD COLUMN IF NOT EXISTS order_type VARCHAR(20)
                        DEFAULT 'delivery' NOT NULL;
                ALTER TABLE website_order
                    ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20)
                        DEFAULT 'cash' NOT NULL;
                ALTER TABLE website_order
                    ADD COLUMN IF NOT EXISTS table_number VARCHAR(30)
                        DEFAULT '' NOT NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
