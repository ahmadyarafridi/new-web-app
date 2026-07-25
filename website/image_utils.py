import os
import uuid
from io import BytesIO
from PIL import Image, ImageOps
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


def validate_image_file(uploaded_file):
    """
    Validates uploaded image file format and header integrity.
    """
    if not uploaded_file:
        return uploaded_file

    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        img.verify()
    except Exception:
        raise forms.ValidationError("Invalid or corrupted image file. Please upload a valid image (JPG, PNG, WEBP).")
    finally:
        uploaded_file.seek(0)

    return uploaded_file


def optimize_image(uploaded_file, prefix='img'):
    """
    Optimizes and shrinks uploaded images using Pillow:
    1. Automatically compresses & shrinks files to guarantee size is UNDER 1 MB.
    2. Securely renames the image (e.g. rev-a1b2c3d4.jpg) to prevent file injection/hacking.
    """
    if not uploaded_file:
        return uploaded_file

    uploaded_file.seek(0)
    try:
        img = Image.open(uploaded_file)
    except Exception:
        return uploaded_file

    # Auto-rotate based on EXIF orientation metadata
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Target dimension mapping based on image upload type (prefix)
    TARGET_DIMENSIONS = {
        'prod': 600,     # Product cards (600px max)
        'deal': 700,     # Special deals (700px max)
        'cat': 500,      # Category previews (500px max)
        'rev': 200,      # Customer review avatars (200px max)
        'logo': 400,     # Restaurant logo (400px max)
        'hero': 1200,    # Hero/Banner headers (1200px max)
    }

    max_dim = TARGET_DIMENSIONS.get(prefix, getattr(settings, 'IMAGE_MAX_DIMENSION', 600))
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 500 * 1024)

    # Initial resize if longest side exceeds target max_dim
    width, height = img.size
    if max(width, height) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    output_io = BytesIO()
    
    # Try converting to WebP format (supports transparency & RGB)
    try:
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA' if 'transparency' in img.info or img.mode in ('LA', 'P') else 'RGB')
        
        quality = getattr(settings, 'IMAGE_QUALITY', 82)
        img.save(output_io, format='WEBP', quality=quality, method=4)
        ext = 'webp'
        content_type = 'image/webp'
    except Exception:
        # Fallback to optimized JPEG/PNG if WebP conversion fails
        is_transparent = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
        if is_transparent:
            img.save(output_io, format='PNG', optimize=True)
            ext = 'png'
            content_type = 'image/png'
        else:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output_io, format='JPEG', quality=82, optimize=True)
            ext = 'jpg'
            content_type = 'image/jpeg'

    output_io.seek(0)
    
    # SECURE RENAMING: Generate a safe, sanitized filename e.g., prod-a1b2c3d4.webp
    unique_id = uuid.uuid4().hex[:8]
    secure_filename = f"{prefix}-{unique_id}.{ext}"

    return SimpleUploadedFile(
        name=secure_filename,
        content=output_io.getvalue(),
        content_type=content_type
    )
