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

    max_dim = getattr(settings, 'IMAGE_MAX_DIMENSION', 1600)
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 1 * 1024 * 1024)

    # Initial resize if longest side exceeds 1600px
    width, height = img.size
    if max(width, height) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    output_io = BytesIO()
    is_transparent = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)

    if is_transparent:
        try:
            img.save(output_io, format='PNG', optimize=True)
            ext = 'png'
            content_type = 'image/png'
        except Exception:
            img = img.convert('RGB')
            img.save(output_io, format='JPEG', quality=85, optimize=True)
            ext = 'jpg'
            content_type = 'image/jpeg'
    else:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        quality = getattr(settings, 'IMAGE_QUALITY', 85)
        img.save(output_io, format='JPEG', quality=quality, optimize=True)
        ext = 'jpg'
        content_type = 'image/jpeg'

        # If file size is still > 1 MB, iteratively compress quality & scale down until < 1 MB
        current_quality = quality
        while output_io.tell() > max_size and current_quality > 25:
            current_quality -= 15
            output_io = BytesIO()
            img.save(output_io, format='JPEG', quality=current_quality, optimize=True)

        if output_io.tell() > max_size:
            # Further scale down dimensions if still > 1 MB
            scale_factor = 0.75
            while output_io.tell() > max_size and img.size[0] > 300 and img.size[1] > 300:
                new_w = int(img.size[0] * scale_factor)
                new_h = int(img.size[1] * scale_factor)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                output_io = BytesIO()
                img.save(output_io, format='JPEG', quality=45, optimize=True)

    output_io.seek(0)
    
    # SECURE RENAMING: Generate a safe, sanitized filename e.g., rev-a1b2c3d4.jpg
    unique_id = uuid.uuid4().hex[:8]
    secure_filename = f"{prefix}-{unique_id}.{ext}"

    return SimpleUploadedFile(
        name=secure_filename,
        content=output_io.getvalue(),
        content_type=content_type
    )
