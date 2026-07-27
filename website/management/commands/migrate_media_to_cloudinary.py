import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from website.models import Category, Product, Deal, Review, CustomerFeedback
from website.image_utils import optimize_image


class Command(BaseCommand):
    help = 'Migrates all existing local media & static database image references to Cloudinary CDN storage.'

    def handle(self, *args, **options):
        if not getattr(settings, 'USE_CLOUDINARY', False):
            self.stdout.write(self.style.ERROR(
                '[ERROR] Cloudinary is not configured in settings. '
                'Please set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET.'
            ))
            return

        self.stdout.write(self.style.SUCCESS('\n=================================================='))
        self.stdout.write(self.style.SUCCESS('   CLOUDINARY MEDIA & STATIC IMAGE MIGRATION'))
        self.stdout.write(self.style.SUCCESS('==================================================\n'))

        counts_by_type = {
            'Products': 0,
            'Categories': 0,
            'Deals': 0,
            'Reviews': 0,
        }
        
        total_migrated = 0
        total_failed = 0
        total_skipped = 0

        models_to_check = [
            (Category, 'image_file', None, 'cat', 'categories', 'Categories'),
            (Product, 'image_file', 'image', 'prod', 'products', 'Products'),
            (Deal, 'image_file', 'image', 'deal', 'deals', 'Deals'),
            (Review, 'avatar_file', 'avatar_url', 'rev', 'reviews', 'Reviews'),
            (CustomerFeedback, 'avatar_file', None, 'rev', 'reviews', 'Reviews'),
        ]

        for model_cls, file_field_name, char_field_name, prefix, folder, display_type in models_to_check:
            records = model_cls.objects.all()
            for record in records:
                file_field = getattr(record, file_field_name, None)
                char_field_val = getattr(record, char_field_name, '') if char_field_name else ''

                # Check if file_field is already a Cloudinary URL
                file_url = str(file_field.url) if (file_field and hasattr(file_field, 'url')) else ''
                if 'cloudinary' in file_url or 'res.cloudinary.com' in file_url:
                    total_skipped += 1
                    self.stdout.write(f'  [SKIPPED - Already Cloudinary] {display_type} (ID: {record.pk}) -> {file_url}')
                    continue

                # Locate local image file (either in media/ or static/)
                local_path = None
                if file_field and file_field.name:
                    path_media = os.path.join(settings.BASE_DIR, 'media', file_field.name)
                    if os.path.exists(path_media):
                        local_path = path_media

                if not local_path and char_field_val:
                    # Check potential static file paths
                    candidate_paths = [
                        os.path.join(settings.BASE_DIR, 'static', char_field_val),
                        os.path.join(settings.BASE_DIR, 'static', char_field_val.lstrip('/')),
                    ]
                    if not char_field_val.startswith('images/') and not char_field_val.startswith('/static/'):
                        candidate_paths.append(os.path.join(settings.BASE_DIR, 'static', 'images', char_field_val))

                    for path in candidate_paths:
                        if os.path.exists(path):
                            local_path = path
                            break

                if local_path and os.path.exists(local_path):
                    try:
                        self.stdout.write(f'  [MIGRATING] {display_type} (ID: {record.pk}, Path: {local_path})...')
                        
                        with open(local_path, 'rb') as f:
                            # Skip re-compression if file is already WebP
                            if local_path.lower().endswith('.webp'):
                                file_to_upload = SimpleUploadedFile(
                                    name=os.path.basename(local_path),
                                    content=f.read(),
                                    content_type='image/webp'
                                )
                            else:
                                file_to_upload = optimize_image(f, prefix=prefix)

                            saved_name = default_storage.save(f"{folder}/{file_to_upload.name}", file_to_upload)
                            setattr(record, file_field_name, saved_name)
                            record.save(update_fields=[file_field_name])
                            
                        counts_by_type[display_type] += 1
                        total_migrated += 1
                        new_url = getattr(record, file_field_name).url
                        self.stdout.write(self.style.SUCCESS(f'    [OK] Uploaded to Cloudinary: {new_url}'))
                    except Exception as e:
                        total_failed += 1
                        self.stdout.write(self.style.ERROR(f'    [FAILED] {local_path}: {e}'))
                else:
                    total_skipped += 1
                    self.stdout.write(self.style.WARNING(f'  [SKIPPED - No local file found] {display_type} (ID: {record.pk})'))

        self.stdout.write(self.style.SUCCESS('\n=================================================='))
        self.stdout.write(self.style.SUCCESS('            CLOUDINARY MIGRATION REPORT'))
        self.stdout.write(self.style.SUCCESS('=================================================='))
        self.stdout.write(f"{'Type':<18} {'Count'}")
        self.stdout.write('--------------------------------------------------')
        for asset_type in ['Products', 'Categories', 'Deals', 'Reviews']:
            self.stdout.write(f"{asset_type:<18} {counts_by_type[asset_type]}")
        self.stdout.write('--------------------------------------------------')
        self.stdout.write(f"{'Total migrated':<18} {total_migrated}")
        self.stdout.write(f"{'Failed':<18} {total_failed}")
        self.stdout.write(f"{'Skipped':<18} {total_skipped}")
        self.stdout.write(self.style.SUCCESS('==================================================\n'))
