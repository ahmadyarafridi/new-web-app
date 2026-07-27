import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from website.models import Category, Product, Deal, Review, CustomerFeedback
from website.image_utils import optimize_image


class Command(BaseCommand):
    help = 'Migrates all existing local media files to Cloudinary CDN storage with detailed progress tracking.'

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
            (Category, 'image_file', 'cat', 'categories'),
            (Product, 'image_file', 'prod', 'products'),
            (Deal, 'image_file', 'deal', 'deals'),
            (Review, 'avatar_file', 'rev', 'reviews'),
            (CustomerFeedback, 'avatar_file', 'rev', 'reviews'),
        ]

        total_found = 0
        migrated_count = 0
        skipped_count = 0
        failed_count = 0

        for model_cls, field_name, prefix, folder in models_to_check:
            records = model_cls.objects.all()
            for record in records:
                file_field = getattr(record, field_name, None)
                if not file_field or not file_field.name:
                    continue

                total_found += 1
                file_url = str(file_field.url) if hasattr(file_field, 'url') else ''

                # Skip if already migrated to Cloudinary
                if 'cloudinary' in file_url or 'res.cloudinary.com' in file_url:
                    skipped_count += 1
                    self.stdout.write(f'  [SKIPPED - Already Cloudinary] {model_cls.__name__} (ID: {record.pk}) -> {file_url}')
                    continue

                # Locate local file
                local_path = os.path.join(settings.BASE_DIR, 'media', file_field.name)
                if not os.path.exists(local_path):
                    # Check if path is relative to BASE_DIR
                    local_path = os.path.join(settings.BASE_DIR, file_field.name)

                if os.path.exists(local_path):
                    try:
                        self.stdout.write(f'  [MIGRATING] {model_cls.__name__} (ID: {record.pk}, File: {file_field.name})...')
                        
                        with open(local_path, 'rb') as f:
                            # Skip re-compression if file is already optimized WebP
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
                            
                        migrated_count += 1
                        new_url = getattr(record, field_name).url
                        self.stdout.write(self.style.SUCCESS(f'    [OK] Uploaded to Cloudinary: {new_url}'))
                    except Exception as e:
                        failed_count += 1
                        self.stdout.write(self.style.ERROR(f'    [FAILED] {file_field.name}: {e}'))
                else:
                    skipped_count += 1
                    self.stdout.write(self.style.WARNING(f'  [SKIPPED - File not found locally] {model_cls.__name__} (ID: {record.pk}, Path: {local_path})'))

        self.stdout.write(self.style.SUCCESS('\n=================================================='))
        self.stdout.write(self.style.SUCCESS('            CLOUDINARY MIGRATION REPORT'))
        self.stdout.write(self.style.SUCCESS('=================================================='))
        self.stdout.write(f'  - Total Images Found:          {total_found}')
        self.stdout.write(f'  - Successfully Migrated:       {migrated_count}')
        self.stdout.write(f'  - Skipped (Already Cloudinary): {skipped_count}')
        self.stdout.write(f'  - Failed:                       {failed_count}')
        self.stdout.write(self.style.SUCCESS('==================================================\n'))
