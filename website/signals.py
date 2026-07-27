from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Category, Product, Deal, Review, CustomerFeedback

# List of models that contain image files
IMAGE_MODELS = [
    (Category, 'image_file'),
    (Product, 'image_file'),
    (Deal, 'image_file'),
    (Review, 'avatar_file'),
    (CustomerFeedback, 'avatar_file'),
]


def _safe_delete_file(file_field):
    """
    Safely deletes a FileField from the active storage (Cloudinary or local disk).
    """
    if file_field and file_field.name:
        try:
            storage = file_field.storage
            if storage.exists(file_field.name):
                storage.delete(file_field.name)
        except Exception as e:
            print(f"[IMAGE CLEANUP WARNING] Could not delete image '{file_field.name}': {e}")


@receiver(post_delete, sender=Category)
@receiver(post_delete, sender=Product)
@receiver(post_delete, sender=Deal)
@receiver(post_delete, sender=Review)
@receiver(post_delete, sender=CustomerFeedback)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes image file from Cloudinary/storage when corresponding database record is deleted.
    """
    for model_cls, field_name in IMAGE_MODELS:
        if isinstance(instance, model_cls):
            file_field = getattr(instance, field_name, None)
            _safe_delete_file(file_field)


@receiver(pre_save, sender=Category)
@receiver(pre_save, sender=Product)
@receiver(pre_save, sender=Deal)
@receiver(pre_save, sender=Review)
@receiver(pre_save, sender=CustomerFeedback)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old image file from Cloudinary/storage when a record's image is updated/replaced.
    """
    if not instance.pk:
        return False

    for model_cls, field_name in IMAGE_MODELS:
        if isinstance(instance, model_cls):
            try:
                old_instance = sender.objects.get(pk=instance.pk)
            except sender.DoesNotExist:
                return False

            old_file = getattr(old_instance, field_name, None)
            new_file = getattr(instance, field_name, None)

            if old_file and old_file != new_file:
                _safe_delete_file(old_file)
