from django import forms
from django.contrib.auth.forms import AuthenticationForm
from website.models import RestaurantInfo, Category, Product, Deal, Review
from website.image_utils import validate_image_file, optimize_image

class OwnerLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'floating-input',
            'placeholder': ' ',
            'id': 'loginUsername',
            'required': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'floating-input',
            'placeholder': ' ',
            'id': 'loginPassword',
            'required': True,
        })
    )


class ProductForm(forms.ModelForm):
    image_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'dashboard-input', 'accept': 'image/*'})
    )

    class Meta:
        model = Product
        fields = ['category', 'name', 'price', 'description', 'image_file', 'is_available']
        labels = {
            'is_available': 'In Stock',
        }
        widgets = {
            'category': forms.Select(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'name': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'price': forms.NumberInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'description': forms.Textarea(attrs={'class': 'floating-input', 'rows': 2, 'placeholder': ' '}),
            'is_available': forms.CheckboxInput(attrs={'class': 'dashboard-checkbox', 'style': 'width: 18px; height: 18px; accent-color: var(--color-primary); cursor: pointer;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all().order_by('display_order', 'name')
        self.fields['category'].empty_label = None

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean_image_file(self):
        image_file = self.cleaned_data.get('image_file')
        if image_file:
            validate_image_file(image_file)
            image_file = optimize_image(image_file, prefix='prod')
        return image_file

    def clean(self):
        cleaned_data = super().clean()
        image_file = cleaned_data.get('image_file')
        if 'image_file' not in self.errors:
            if not self.instance.pk and not image_file:
                self.add_error('image_file', "Product image is required when creating a product.")
            elif self.instance.pk and not image_file and not self.instance.image_file and not self.instance.image:
                self.add_error('image_file', "Product image is required.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        from django.utils.text import slugify
        import uuid
        if not instance.slug and instance.name:
            instance.slug = slugify(instance.name) or f"prod-{uuid.uuid4().hex[:6]}"
        
        # Ensure unique slug
        original_slug = instance.slug
        counter = 1
        while Product.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1

        if not instance.item_code:
            instance.item_code = f"prod-{uuid.uuid4().hex[:6]}"
        else:
            original_code = instance.item_code
            code_counter = 1
            while Product.objects.filter(item_code=instance.item_code).exclude(pk=instance.pk).exists():
                instance.item_code = f"{original_code}-{code_counter}"
                code_counter += 1

        # Set display_order to 0 ONLY for brand new items (not when editing existing items)
        if not instance.pk:
            instance.display_order = 0
        if commit:
            instance.save()
        return instance


class CategoryForm(forms.ModelForm):
    display_order = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
        label="Order Position"
    )
    image_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'dashboard-input', 'accept': 'image/*'})
    )

    class Meta:
        model = Category
        fields = ['name', 'display_order', 'image_file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
        }

    def clean_image_file(self):
        image_file = self.cleaned_data.get('image_file')
        if image_file:
            validate_image_file(image_file)
            image_file = optimize_image(image_file, prefix='cat')
        return image_file

    def save(self, commit=True):
        instance = super().save(commit=False)
        from django.utils.text import slugify
        from django.db.models import Max, F
        import uuid

        if not instance.slug and instance.name:
            instance.slug = slugify(instance.name) or f"cat-{uuid.uuid4().hex[:6]}"
        
        # Ensure unique slug
        original_slug = instance.slug
        counter = 1
        while Category.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1

        is_new = instance.pk is None
        requested_order = self.cleaned_data.get('display_order')

        if is_new:
            max_order = Category.objects.aggregate(Max('display_order'))['display_order__max'] or 0
            if requested_order is None or requested_order <= 0:
                target_order = max_order + 1
            else:
                target_order = requested_order

            # Shift all categories with order >= target_order down by +1
            Category.objects.filter(display_order__gte=target_order).update(display_order=F('display_order') + 1)
            instance.display_order = target_order
            instance.is_active = True
        else:
            old_order = Category.objects.get(pk=instance.pk).display_order
            if requested_order is not None and requested_order > 0 and requested_order != old_order:
                target_order = requested_order
                if target_order < old_order:
                    Category.objects.filter(
                        display_order__gte=target_order,
                        display_order__lt=old_order
                    ).exclude(pk=instance.pk).update(display_order=F('display_order') + 1)
                else:
                    Category.objects.filter(
                        display_order__gt=old_order,
                        display_order__lte=target_order
                    ).exclude(pk=instance.pk).update(display_order=F('display_order') - 1)
                
                instance.display_order = target_order

        if commit:
            instance.save()
        return instance


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ['title', 'price', 'description', 'image_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'price': forms.NumberInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'description': forms.Textarea(attrs={'class': 'floating-input', 'rows': 2, 'placeholder': ' '}),
            'image_file': forms.FileInput(attrs={'class': 'dashboard-input', 'accept': 'image/*'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean_image_file(self):
        image_file = self.cleaned_data.get('image_file')
        if image_file:
            validate_image_file(image_file)
            image_file = optimize_image(image_file, prefix='deal')
        return image_file

    def save(self, commit=True):
        instance = super().save(commit=False)
        from django.db.models import Max
        import uuid
        if not instance.item_code:
            instance.item_code = f"DEAL-{uuid.uuid4().hex[:6].upper()}"
        if not instance.pk:
            max_order = Deal.objects.aggregate(Max('display_order'))['display_order__max']
            instance.display_order = (max_order or 0) + 1
            instance.is_active = True
        if commit:
            instance.save()
        return instance


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['customer_name', 'reviewer_role', 'rating', 'comment', 'avatar_url', 'avatar_file', 'is_approved', 'display_order']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'reviewer_role': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'rating': forms.NumberInput(attrs={'class': 'floating-input', 'placeholder': ' ', 'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'class': 'floating-input', 'rows': 3, 'placeholder': ' '}),
            'avatar_url': forms.URLInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'avatar_file': forms.FileInput(attrs={'class': 'dashboard-input', 'accept': 'image/*'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'dashboard-checkbox'}),
            'display_order': forms.NumberInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is not None and (rating < 1 or rating > 5):
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating

    def clean_avatar_file(self):
        avatar_file = self.cleaned_data.get('avatar_file')
        if avatar_file:
            validate_image_file(avatar_file)
            avatar_file = optimize_image(avatar_file, prefix='rev')
        return avatar_file


class RestaurantInfoForm(forms.ModelForm):
    class Meta:
        model = RestaurantInfo
        fields = [
            'name', 'tagline', 'phone', 'whatsapp_number', 'email', 'address',
            'google_maps_plus_code', 'google_rating', 'google_reviews_count',
            'opening_hours_text', 'lunch_hours', 'dinner_hours',
            'hero_description', 'about_established_year', 'about_history',
            'about_history_p2', 'about_quality_promise'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'tagline': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'phone': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'email': forms.EmailInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'address': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'google_maps_plus_code': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'google_rating': forms.NumberInput(attrs={'class': 'floating-input', 'placeholder': ' ', 'step': '0.1'}),
            'google_reviews_count': forms.NumberInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'opening_hours_text': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'lunch_hours': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'dinner_hours': forms.TextInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'hero_description': forms.Textarea(attrs={'class': 'floating-input', 'rows': 3, 'placeholder': ' '}),
            'about_established_year': forms.NumberInput(attrs={'class': 'floating-input', 'placeholder': ' '}),
            'about_history': forms.Textarea(attrs={'class': 'floating-input', 'rows': 3, 'placeholder': ' '}),
            'about_history_p2': forms.Textarea(attrs={'class': 'floating-input', 'rows': 3, 'placeholder': ' '}),
            'about_quality_promise': forms.Textarea(attrs={'class': 'floating-input', 'rows': 3, 'placeholder': ' '}),
        }

    def clean_google_rating(self):
        rating = self.cleaned_data.get('google_rating')
        if rating is not None and (rating < 0 or rating > 5):
            raise forms.ValidationError("Google Rating must be between 0 and 5.")
        return rating
