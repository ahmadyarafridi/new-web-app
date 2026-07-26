from .models import RestaurantInfo
from django.db import OperationalError, ProgrammingError

def restaurant_info(request):
    try:
        info = RestaurantInfo.objects.first()
        if info and (info.name == "Delicious Food Stop" or info.address != "Amazing foods jamrud"):
            info.name = "Amazing Foods"
            info.address = "Amazing foods jamrud"
            if info.about_history and "Delicious Food Stop" in info.about_history:
                info.about_history = info.about_history.replace("Delicious Food Stop", "Amazing Foods")
            info.save()
    except (OperationalError, ProgrammingError):
        info = None
    if not info:
        # Fallback default info object if database isn't seeded yet
        info = RestaurantInfo()
    return {
        'restaurant': info
    }
