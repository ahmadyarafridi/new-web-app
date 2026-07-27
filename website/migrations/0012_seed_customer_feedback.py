from django.db import migrations


def seed_feedback(apps, schema_editor):
    CustomerFeedback = apps.get_model('website', 'CustomerFeedback')
    Review = apps.get_model('website', 'Review')

    feedback_data = [
        {
            'customer_name': 'Zainab Khan',
            'rating': 5,
            'comment': '"The best Zinger burgers in Jamrud! Always hot, crispy, and fresh. Fast WhatsApp ordering saves time!"',
            'status': 'approved'
        },
        {
            'customer_name': 'Hamza Afridi',
            'rating': 5,
            'comment': '"Authentic local shawarma and amazing wood-fired pizzas. Great atmosphere and friendly team!"',
            'status': 'approved'
        },
        {
            'customer_name': 'Muhammad Ali',
            'rating': 5,
            'comment': '"Their Special Chicken Pulao is unbeatable in flavor. Great quality family deals!"',
            'status': 'approved'
        },
    ]

    for fbdata in feedback_data:
        CustomerFeedback.objects.update_or_create(
            customer_name=fbdata['customer_name'],
            defaults={
                'rating': fbdata['rating'],
                'comment': fbdata['comment'],
                'status': fbdata['status'],
            }
        )
        Review.objects.update_or_create(
            customer_name=fbdata['customer_name'],
            defaults={
                'rating': fbdata['rating'],
                'comment': fbdata['comment'],
                'is_approved': True,
            }
        )


def reverse_feedback(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0011_update_reviews_concise'),
    ]

    operations = [
        migrations.RunPython(seed_feedback, reverse_feedback),
    ]
