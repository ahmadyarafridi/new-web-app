from django.db import migrations


def repair_legacy_order_columns(apps, schema_editor):
    Order = apps.get_model('website', 'Order')
    existing_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(), Order._meta.db_table
        )
    }

    for field_name in ('order_type', 'payment_method', 'table_number'):
        field = Order._meta.get_field(field_name)
        if field.column not in existing_columns:
            schema_editor.add_field(Order, field)


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0019_ensure_order_columns_railway_fix'),
    ]

    operations = [
        migrations.RunPython(
            code=repair_legacy_order_columns,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
