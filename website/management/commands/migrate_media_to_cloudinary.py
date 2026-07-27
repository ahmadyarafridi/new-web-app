import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from website.models import Category, Product, Deal, Review, CustomerFeedback
from website.image_utils import optimize_image


class Command(BaseCommand):
    help = 'Safely migrates local media files from MEDIA_ROOT to Cloudinary storage after optimizing with Pillow.'

    def handle(self, *args, **options):
        if not getattr(settings, 'USE_CLOUDINARY', False):
            self.stdout.write(self.style.ERROR(
                '[ERROR] Cloudinary is not configured in settings. '
                'Please set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET first.'
            ))
            return

        self.stdout.write(self.style.SUCCESS('[START] Migrating local media files to Cloudinary...'))
        
        models_to_check = [
            (Category, 'image_file', 'cat'),
            (Product, 'image_file', 'prod'),
            (Deal, 'image_file', 'deal'),
            (Review, 'avatar_file', 'rev'),
            (CustomerFeedback, 'avatar_file', 'rev'),
        ]

        migrated_count = 0
        skipped_count = 0

        for model_cls, field_name, prefix in models_to_check:
            records = model_cls.objects.all()
            for record in records:
                file_field = getattr(record, field_name, None)
                if not file_field or not file_field.name:
                    continue

                # Check if file URL is already a Cloudinary URL
                file_url = str(file_field.url) if hasattr(file_field, 'url') else ''
                if 'cloudinary' in file_url or 'res.cloudinary.com' in file_url:
                    skipped_count += 1
                    continue

                # Check local media file path
                local_path = os.path.join(settings.BASE_DIR, 'media', file_field.name)
                if os.path.exists(local_path):
                    try:
                        self.stdout.write(f'  - Uploading {model_cls.__name__} (ID: {record.pk}, File: {file_field.name})...')
                        
                        with open(local_path, 'rb') as f:
                            # Skip re-compression if file is already WebP
                            if file_field.name.lower().endswith('.webp'):
                                from django.core.files.uploadedfile import SimpleUploadedFile
                                file_to_upload = SimpleUploadedFile(
                                    name=os.path.basename(file_field.name),
                                    content=f.read(),
                                    content_type='image/webp'
                                )
                            else:
                                file_to_upload = optimize_image(f, prefix=prefix)

                            saved_name = default_storage.save(f"{prefix}s/{file_to_upload.name}", file_to_upload)
                            setattr(record, field_name, saved_name)
                            record.save(update_fields=[field_name])
                            
                        migrated_count += 1
                        self.stdout.write(self.style.SUCCESS(f'    [OK] Uploaded to Cloudinary: {saved_name}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'    [FAILED] {file_field.name}: {e}'))
                else:
                    skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n[COMPLETE] Migration finished! Migrated: {migrated_count} files, Skipped/Already Cloudinary: {skipped_count} files.'
        ))
