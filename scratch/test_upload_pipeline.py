import os
import django
from PIL import Image

import sys
sys.path.insert(0, r'd:\Coding\HTML_CSS_JavaScript\Restaurant_Website')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_config.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from website.image_utils import optimize_image

# Create a test high-res image (3000x2000 px) in memory
test_img = Image.new('RGB', (3000, 2000), color='red')
from io import BytesIO
buf = BytesIO()
test_img.save(buf, format='JPEG', quality=95)
buf.seek(0)

uploaded = SimpleUploadedFile("raw_test_photo.jpg", buf.getvalue(), content_type="image/jpeg")
print(f"Original test image size: {len(uploaded.read()) / 1024.0:.1f} KB")

# Process with optimize_image
res = optimize_image(uploaded, prefix='test_prod')
res_data = res.read()
print(f"Optimized image filename: {res.name}")
print(f"Optimized image size: {len(res_data) / 1024.0:.1f} KB")

# Verify dimension and format using PIL
with Image.open(BytesIO(res_data)) as result_img:
    print(f"Optimized dimensions: {result_img.size[0]}x{result_img.size[1]} (Max allowed: 800px)")
    print(f"Optimized format: {result_img.format}")
    assert max(result_img.size) <= 800
    print("[SUCCESS] Upload pipeline test passed cleanly!")
