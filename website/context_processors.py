from .models import RestaurantInfo

def restaurant_info(request):
    info = RestaurantInfo.objects.first()
    if not info:
        # Fallback default info object if database isn't seeded yet
        info = RestaurantInfo()
    return {
        'restaurant': info
    }
