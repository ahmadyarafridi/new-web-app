from .models import RestaurantInfo
from django.db import OperationalError, ProgrammingError

def restaurant_info(request):
    try:
        info = RestaurantInfo.objects.first()
    except (OperationalError, ProgrammingError):
        info = None
    
    if not info:
        info = RestaurantInfo(name="Amazing Foods", address="Amazing Foods Peshawar")
    else:
        info.name = "Amazing Foods"
        info.address = "Amazing Foods Peshawar"
        if info.about_history and "Delicious Food Stop" in info.about_history:
            info.about_history = info.about_history.replace("Delicious Food Stop", "Amazing Foods")
        if info.about_history and "Jamrud" in info.about_history:
            info.about_history = info.about_history.replace("Jamrud", "Peshawar")
        if info.hero_description and "Jamrud" in info.hero_description:
            info.hero_description = info.hero_description.replace("Jamrud", "Peshawar")

    return {
        'restaurant': info
    }
