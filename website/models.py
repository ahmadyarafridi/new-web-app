from django.db import models
from django.utils import timezone

class DailyVisit(models.Model):
    date = models.DateField(default=timezone.now, unique=True)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date}: {self.count} visits"


class RestaurantInfo(models.Model):
    name = models.CharField(max_length=100, default="Amazing Foods")
    tagline = models.CharField(max_length=255, default="Fast Food & Pulao")
    phone = models.CharField(max_length=20, default="+92 323 2870355")
    whatsapp_number = models.CharField(max_length=20, default="923232870355")
    email = models.EmailField(default="info@amazingfoods.pk")
    address = models.CharField(max_length=255, default="Amazing foods jamrud")
    google_maps_plus_code = models.CharField(max_length=50, default="292F+QRP Jamrud")
    google_rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.4)
    google_reviews_count = models.IntegerField(default=39)
    opening_hours_text = models.CharField(max_length=100, default="Monday – Sunday: 11:00 AM – 10:00 PM")
    lunch_hours = models.CharField(max_length=100, default="11:00 AM – 4:00 PM")
    dinner_hours = models.CharField(max_length=100, default="5:00 PM – 10:00 PM")
    is_open = models.BooleanField(default=True, help_text="Switch between OPEN and CLOSED for online ordering")
    
    # Hero & About Page content
    hero_description = models.TextField(default="Experience the finest fast food in Jamrud. From wood-fired pizzas and local shawarmas to aromatic chicken pulao, we cook every deal fresh with premium ingredients.")
    about_established_year = models.IntegerField(default=2018)
    about_history = models.TextField(default="Amazing Foods opened in Jamrud in 2018 to serve flavorful, high-quality fast food—from wood-fired pizzas and shawarmas to crispy zinger burgers and aromatic chicken pulao.")
    about_history_p2 = models.TextField(default="We source fresh local ingredients, dry-age our beef in-house, and bake pizza dough from scratch daily to make every bite memorable.")
    about_quality_promise = models.TextField(default="All of our signature sauces and dips are prepared fresh by our chefs every single morning. We select fresh farm veggies and premium meats, bringing you gourmet quality at fast-food convenience. Drop by today and taste the difference!")
    
    class Meta:
        verbose_name = "Restaurant Information"
        verbose_name_plural = "Restaurant Information"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    image_file = models.FileField(upload_to='categories/', blank=True, null=True, help_text="Category image file")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.CharField(max_length=255, help_text="Image path e.g. static/images/burger.jpg")
    image_file = models.FileField(upload_to='products/', blank=True, null=True, help_text="Or upload image file directly")
    tag = models.CharField(max_length=50, blank=True, help_text="e.g., Popular, Bestseller, Chef's Special, Spicy, Crispy")
    item_code = models.CharField(max_length=50, unique=True, help_text="Unique HTML data-id for shopping cart e.g. pizza-tikka")
    custom_style = models.CharField(max_length=255, blank=True, help_text="Inline CSS filters e.g. filter: hue-rotate(45deg);")
    is_available = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        import uuid
        if not self.slug and self.name:
            self.slug = slugify(self.name) or f"prod-{uuid.uuid4().hex[:6]}"
        
        # Ensure unique slug
        original_slug = self.slug
        counter = 1
        while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1

        # Ensure unique item_code
        if not self.item_code:
            self.item_code = f"prod-{uuid.uuid4().hex[:6]}"
        else:
            original_code = self.item_code
            code_counter = 1
            while Product.objects.filter(item_code=self.item_code).exclude(pk=self.pk).exists():
                self.item_code = f"{original_code}-{code_counter}"
                code_counter += 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Rs. {self.price:.0f})"

    @property
    def image_src(self):
        if self.image_file:
            return self.image_file.url
        return self.image


class Deal(models.Model):
    title = models.CharField(max_length=150)
    item_code = models.CharField(max_length=50, unique=True, help_text="e.g. deal-zinger-combo")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.CharField(max_length=255)
    image_file = models.FileField(upload_to='deals/', blank=True, null=True, help_text="Or upload deal image file directly")
    tag = models.CharField(max_length=50, blank=True, help_text="e.g. Bestseller Deal, Hot Deal, Family Saver")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.title} (Rs. {self.price:.0f})"

    @property
    def image_src(self):
        if self.image_file:
            return self.image_file.url
        return self.image


class Review(models.Model):
    customer_name = models.CharField(max_length=100)
    reviewer_role = models.CharField(max_length=100, default="Regular Diner")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    avatar_url = models.URLField(max_length=255, default="https://i.pravatar.cc/120?img=33")
    avatar_file = models.FileField(upload_to='reviews/', blank=True, null=True, help_text="Or upload avatar image file directly")
    is_approved = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'customer_name']

    def __str__(self):
        return f"{self.customer_name} ({self.rating}★)"

    @property
    def avatar_src(self):
        if self.avatar_file:
            return self.avatar_file.url
        return self.avatar_url


class CustomerFeedback(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    customer_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    avatar_file = models.FileField(upload_to='reviews/', blank=True, null=True, help_text="Uploaded customer photo/avatar")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Customer Feedback'

    def __str__(self):
        return f"{self.customer_name} ({self.rating}★) [{self.status.upper()}]"

    @property
    def avatar_src(self):
        if self.avatar_file:
            return self.avatar_file.url
        name_lower = self.customer_name.lower()
        if 'zainab' in name_lower:
            return 'https://i.pravatar.cc/120?img=33'
        elif 'hamza' in name_lower:
            return 'https://i.pravatar.cc/120?img=12'
        elif 'muhammad' in name_lower:
            return 'https://i.pravatar.cc/120?img=68'
        return f'https://i.pravatar.cc/120?img={(self.id * 7) % 70 + 1}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]

    order_id = models.CharField(max_length=50, unique=True, db_index=True)
    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=50)
    delivery_address = models.TextField(blank=True, default='')
    order_notes = models.TextField(blank=True, default='')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def items_summary(self):
        item_strings = [f"{item.product_name} x{item.quantity}" for item in self.items.all()]
        return ", ".join(item_strings) if item_strings else "Standard Order"

    def __str__(self):
        return f"{self.order_id} - {self.customer_name} (Rs. {self.total_price:.0f}) [{self.order_status.upper()}]"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=150)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} (Rs. {self.subtotal:.0f})"


class OrderNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_order', 'New Order'),
        ('status_change', 'Status Change'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True, default='')
    customer_name = models.CharField(max_length=120, blank=True, default='')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='new_order')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - Read: {self.is_read}"
