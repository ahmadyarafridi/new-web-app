from django.db import migrations


def update_reviews(apps, schema_editor):
    Review = apps.get_model('website', 'Review')
    
    reviews_data = [
        {
            'customer_name': 'Zainab Khan',
            'comment': '"The best Zinger burgers in Jamrud! Always hot, crispy, and fresh. Fast WhatsApp ordering saves time!"'
        },
        {
            'customer_name': 'Hamza Afridi',
            'comment': '"Authentic local shawarma and amazing wood-fired pizzas. Great atmosphere and friendly team!"'
        },
        {
            'customer_name': 'Muhammad Ali',
            'comment': '"Their Special Chicken Pulao is unbeatable in flavor. Great quality family deals!"'
        },
    ]
    
    for rdata in reviews_data:
        Review.objects.filter(customer_name=rdata['customer_name']).update(comment=rdata['comment'])


def reverse_reviews(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0010_update_restaurant_name_address'),
    ]

    operations = [
        migrations.RunPython(update_reviews, reverse_reviews),
    ]
