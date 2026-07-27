import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from website.models import Category, Product, Deal, Review, CustomerFeedback
from website.image_utils import optimize_image


class Command(BaseCommand):
    help = 'Migrates all existing local media files to Cloudinary CDN storage with a tabular breakdown report.'

    def handle(self, *args, **options):
        if not getattr(settings, 'USE_CLOUDINARY', False):
            self.stdout.write(self.style.ERROR(
                '[ERROR] Cloudinary is not configured in settings. '
                'Please set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET.'
            ))
            return

        self.stdout.write(self.style.SUCCESS('\n=================================================='))
        self.stdout.write(self.style.SUCCESS('   CLOUDINARY MEDIA MIGRATION IN PROGRESS'))
        self.stdout.write(self.style.SUCCESS('==================================================\n'))
        
        models_to_check = [
            (Category, 'image_file', 'cat', 'categories', 'Categories'),
            (Product, 'image_file', 'prod', 'products', 'Products'),
            (Deal, 'image_file', 'deal', 'deals', 'Deals'),
            (Review, 'avatar_file', 'rev', 'reviews', 'Reviews'),
            (CustomerFeedback, 'avatar_file', 'rev', 'reviews', 'Reviews'),
        ]

        counts_by_type = {
            'Products': 0,
            'Categories': 0,
            'Deals': 0,
            'Reviews': 0,
        }
        
        total_migrated = 0
        total_failed = 0
        total_skipped = 0

        for model_cls, field_name, prefix, folder, display_type in models_to_check:
            records = model_cls.objects.all()
            for record in records:
                file_field = getattr(record, field_name, None)
                if not file_field or not file_field.name:
                    continue

                file_url = str(file_field.url) if hasattr(file_field, 'url') else ''

                # Skip if already migrated to Cloudinary
                if 'cloudinary' in file_url or 'res.cloudinary.com' in file_url:
                    total_skipped += 1
                    self.stdout.write(f'  [SKIPPED - Already Cloudinary] {display_type} (ID: {record.pk}) -> {file_url}')
                    continue

                # Locate local file
                local_path = os.path.join(settings.BASE_DIR, 'media', file_field.name)
                if not os.path.exists(local_path):
                    local_path = os.path.join(settings.BASE_DIR, file_field.name)

                if os.path.exists(local_path):
                    try:
                        self.stdout.write(f'  [MIGRATING] {display_type} (ID: {record.pk}, File: {file_field.name})...')
                        
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

                            saved_name = default_storage.save(f"{folder}/{file_to_upload.name}", file_to_upload)
                            setattr(record, field_name, saved_name)
                            record.save(update_fields=[field_name])
                            
                        counts_by_type[display_type] += 1
                        total_migrated += 1
                        new_url = getattr(record, field_name).url
                        self.stdout.write(self.style.SUCCESS(f'    [OK] Uploaded to Cloudinary: {new_url}'))
                    except Exception as e:
                        total_failed += 1
                        self.stdout.write(self.style.ERROR(f'    [FAILED] {file_field.name}: {e}'))
                else:
                    total_skipped += 1
                    self.stdout.write(self.style.WARNING(f'  [SKIPPED - File not found locally] {display_type} (ID: {record.pk}, Path: {local_path})'))

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
        self.stdout.write(self.style.SUCCESS('==================================================\n'))
