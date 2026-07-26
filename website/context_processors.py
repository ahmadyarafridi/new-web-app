from .models import RestaurantInfo
from django.db import OperationalError, ProgrammingError

def restaurant_info(request):
    try:
        info = RestaurantInfo.objects.first()
    except (OperationalError, ProgrammingError):
        info = None
    
    if not info:
        info = RestaurantInfo(name="Amazing Foods", address="Amazing foods jamrud")
    else:
        info.name = "Amazing Foods"
        info.address = "Amazing foods jamrud"
        if info.about_history and "Delicious Food Stop" in info.about_history:
            info.about_history = info.about_history.replace("Delicious Food Stop", "Amazing Foods")

    return {
        'restaurant': info
    }
