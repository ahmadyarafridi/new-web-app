"""Compatibility checks for legacy production order tables."""

from functools import lru_cache

from django.db import connection


@lru_cache(maxsize=1)
def ensure_order_columns():
    """Add order columns that may be absent on a partially migrated database.

    Railway deployments created before the POS feature can have migration
    history that does not match the physical ``website_order`` table. This is
    deliberately safe to call before creating an order; after one successful
    check, each application worker caches the result.
    """
    from .models import Order

    table_name = Order._meta.db_table
    existing_columns = {
        column.name
        for column in connection.introspection.get_table_description(
            connection.cursor(), table_name
        )
    }

    missing_fields = [
        Order._meta.get_field(field_name)
        for field_name in ('order_type', 'payment_method', 'table_number')
        if Order._meta.get_field(field_name).column not in existing_columns
    ]

    if not missing_fields:
        return

    with connection.schema_editor() as schema_editor:
        for field in missing_fields:
            schema_editor.add_field(Order, field)
