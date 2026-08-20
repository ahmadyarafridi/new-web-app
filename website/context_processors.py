from .models import RestaurantInfo
from django.db import OperationalError, ProgrammingError
from django.conf import settings

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
        info.google_maps_plus_code = "Peshawar, Pakistan"
        if info.about_history and "Delicious Food Stop" in info.about_history:
            info.about_history = info.about_history.replace("Delicious Food Stop", "Amazing Foods")
        if info.about_history and "Jamrud" in info.about_history:
            info.about_history = info.about_history.replace("Jamrud", "Peshawar")
        if info.hero_description and "Jamrud" in info.hero_description:
            info.hero_description = info.hero_description.replace("Jamrud", "Peshawar")

    # Cloudinary CDN helper for hero assets in production
    cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', None)
    use_cloudinary = getattr(settings, 'USE_CLOUDINARY', False) and bool(cloud_name)

    hero_assets_urls = None
    if use_cloudinary:
        base_url = f"https://res.cloudinary.com/{cloud_name}"
        # Transformations: q_auto:low = auto quality (lower), vc_auto = auto video codec,
        # br_600k/br_800k = max bitrate cap, w_1280 = max width for WebM/MP4
        # Posters: q_auto:good, w_1280, f_jpg for fast-loading preview images
        hero_assets_urls = {
            'burger_poster': f"{base_url}/image/upload/q_auto:good,w_1280,f_jpg/v1/hero_videos/burger-poster.jpg",
            'burger_mp4':   f"{base_url}/video/upload/q_auto:low,vc_auto,br_800k,w_1280/v1/hero_videos/Explode_Burger.mp4",
            'burger_webm':  f"{base_url}/video/upload/q_auto:low,vc_auto,br_600k,w_1280/v1/hero_videos/Explode_Burger.webm",
            'pizza_poster': f"{base_url}/image/upload/q_auto:good,w_1280,f_jpg/v1/hero_videos/pizza-poster.jpg",
            'pizza_mp4':    f"{base_url}/video/upload/q_auto:low,vc_auto,br_800k,w_1280/v1/hero_videos/Explode_Pizza.mp4",
            'pizza_webm':   f"{base_url}/video/upload/q_auto:low,vc_auto,br_600k,w_1280/v1/hero_videos/Explode_Pizza.webm",
        }

    return {
        'restaurant': info,
        'hero_assets': hero_assets_urls
    }
