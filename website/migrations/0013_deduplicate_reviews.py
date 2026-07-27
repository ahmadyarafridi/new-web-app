from django.db import migrations


def deduplicate_reviews(apps, schema_editor):
    Review = apps.get_model('website', 'Review')
    CustomerFeedback = apps.get_model('website', 'CustomerFeedback')

    # Remove all CustomerFeedback duplicates to keep single source of truth
    CustomerFeedback.objects.all().delete()

    # Deduplicate Review model by customer_name
    seen_names = set()
    for r in Review.objects.all().order_by('id'):
        if r.customer_name in seen_names:
            r.delete()
        else:
            seen_names.add(r.customer_name)


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0012_seed_customer_feedback'),
    ]

    operations = [
        migrations.RunPython(deduplicate_reviews, reverse_func),
    ]
