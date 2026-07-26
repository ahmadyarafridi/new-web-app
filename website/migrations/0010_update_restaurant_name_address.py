from django.db import migrations

def update_restaurant_info(apps, schema_editor):
    RestaurantInfo = apps.get_model('website', 'RestaurantInfo')
    info = RestaurantInfo.objects.first()
    if info:
        info.name = "Amazing Foods"
        info.address = "Amazing foods jamrud"
        if info.about_history and "Delicious Food Stop" in info.about_history:
            info.about_history = info.about_history.replace("Delicious Food Stop", "Amazing Foods")
        info.save()

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0009_customerfeedback_avatar_file'),
    ]

    operations = [
        migrations.RunPython(update_restaurant_info, reverse_code=migrations.RunPython.noop),
    ]
