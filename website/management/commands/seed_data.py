from django.core.management.base import BaseCommand
from website.models import RestaurantInfo, Category, Product, Deal, Review

class Command(BaseCommand):
    help = 'Seeds initial restaurant data into database'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database with restaurant data...')

        # 1. Restaurant Information
        info, created = RestaurantInfo.objects.get_or_create(id=1)
        info.name = "Delicious Food Stop"
        info.tagline = "Fast Food & Pulao"
        info.phone = "+92 333 9342567"
        info.whatsapp_number = "923339342567"
        info.email = "info@deliciousfoodstop.pk"
        info.address = "Jamrud, Khyber District, Khyber Pakhtunkhwa, Pakistan"
        info.google_maps_plus_code = "292F+QRP Jamrud"
        info.google_rating = 4.4
        info.google_reviews_count = 39
        info.opening_hours_text = "Monday – Sunday: 11:00 AM – 10:00 PM"
        info.lunch_hours = "11:00 AM – 4:00 PM"
        info.dinner_hours = "5:00 PM – 10:00 PM"
        info.hero_description = "Experience the finest fast food in Jamrud. From wood-fired pizzas and local shawarmas to aromatic chicken pulao, we cook every deal fresh with premium ingredients."
        info.about_established_year = 2018
        info.about_history = "Delicious Food Stop opened in Jamrud in 2018 to serve flavorful, high-quality fast food—from wood-fired pizzas and shawarmas to crispy zinger burgers and aromatic chicken pulao."
        info.about_history_p2 = "We source fresh local ingredients, dry-age our beef in-house, and bake pizza dough from scratch daily to make every bite memorable."
        info.about_quality_promise = "All of our signature sauces and dips are prepared fresh by our chefs every single morning. We select fresh farm veggies and premium meats, bringing you gourmet quality at fast-food convenience. Drop by today and taste the difference!"
        info.save()
        self.stdout.write(self.style.SUCCESS('[OK] RestaurantInfo updated'))

        # 2. Categories
        categories_data = [
            {'name': 'Special Deals', 'slug': 'deals', 'order': 1},
            {'name': 'Pizzas', 'slug': 'pizzas', 'order': 2},
            {'name': 'Shawarma & Burgers', 'slug': 'shawarma-burgers', 'order': 3},
            {'name': 'Sides & Wings', 'slug': 'sides-wings', 'order': 4},
            {'name': 'Traditional Pulao', 'slug': 'traditional-pulao', 'order': 5},
            {'name': 'Beverages', 'slug': 'beverages', 'order': 6},
        ]
        
        cat_objs = {}
        for cdata in categories_data:
            cat, _ = Category.objects.update_or_create(
                slug=cdata['slug'],
                defaults={'name': cdata['name'], 'display_order': cdata['order'], 'is_active': True}
            )
            cat_objs[cdata['slug']] = cat
        self.stdout.write(self.style.SUCCESS('[OK] Categories created/updated'))

        # 3. Special Deals
        deals_data = [
            {
                'title': 'Zinger Combo Deal',
                'item_code': 'deal-zinger-combo',
                'price': 450,
                'description': 'Crispy Zinger Burger + French Fries + Cold Drink',
                'image': 'images/burger.jpg',
                'tag': 'Bestseller Deal',
                'order': 1
            },
            {
                'title': 'Couple Pizza Deal',
                'item_code': 'deal-couple-pizza',
                'price': 899,
                'description': 'Medium Tikka Pizza + 2 Chilled Soft Drinks',
                'image': 'images/pizza.jpg',
                'tag': 'Hot Deal',
                'order': 2
            },
            {
                'title': 'Mega Family Deal',
                'item_code': 'deal-mega-family',
                'price': 1650,
                'description': 'Large Fajita Pizza + Special Chicken Pulao + 1.5L Soda',
                'image': 'images/Menu/Main Courses/Beef Steak.jpg',
                'tag': 'Family Saver',
                'order': 3
            },
            {
                'title': 'Shawarma Feast Deal',
                'item_code': 'deal-shawarma-feast',
                'price': 580,
                'description': '2 Chicken Shawarmas + Hot Wings (6 pcs) + 2 Lime Sodas',
                'image': 'images/Menu/Appetizers/Chicken Wings.jpg',
                'tag': 'Special',
                'order': 4
            },
        ]

        for ddata in deals_data:
            Deal.objects.update_or_create(
                item_code=ddata['item_code'],
                defaults={
                    'title': ddata['title'],
                    'price': ddata['price'],
                    'description': ddata['description'],
                    'image': ddata['image'],
                    'tag': ddata['tag'],
                    'display_order': ddata['order'],
                    'is_active': True
                }
            )
        self.stdout.write(self.style.SUCCESS('[OK] Special Deals created/updated'))

        # 4. Menu Products
        products_data = [
            # Deals inside menu
            {
                'cat': 'deals',
                'name': 'Zinger Combo Deal',
                'slug': 'menu-deal-zinger-combo',
                'price': 450,
                'description': 'Crispy Zinger Burger + French Fries + Cold Drink',
                'image': 'images/burger.jpg',
                'tag': 'Bestseller Deal',
                'item_code': 'deal-zinger-combo',
                'order': 1
            },
            {
                'cat': 'deals',
                'name': 'Couple Pizza Deal',
                'slug': 'menu-deal-couple-pizza',
                'price': 899,
                'description': 'Medium Tikka Pizza + 2 Chilled Soft Drinks',
                'image': 'images/pizza.jpg',
                'tag': 'Hot Deal',
                'item_code': 'deal-couple-pizza',
                'order': 2
            },
            {
                'cat': 'deals',
                'name': 'Mega Family Deal',
                'slug': 'menu-deal-mega-family',
                'price': 1650,
                'description': 'Large Fajita Pizza + Special Chicken Pulao + 1.5L Soda',
                'image': 'images/Menu/Main Courses/Beef Steak.jpg',
                'tag': 'Family Saver',
                'item_code': 'deal-mega-family',
                'order': 3
            },
            {
                'cat': 'deals',
                'name': 'Shawarma Feast Deal',
                'slug': 'menu-deal-shawarma-feast',
                'price': 580,
                'description': '2 Chicken Shawarmas + Hot Wings (6 pcs) + 2 Lime Sodas',
                'image': 'images/Menu/Appetizers/Chicken Wings.jpg',
                'tag': 'Special',
                'item_code': 'deal-shawarma-feast',
                'order': 4
            },

            # Pizzas
            {
                'cat': 'pizzas',
                'name': 'Chicken Tikka Pizza',
                'slug': 'pizza-tikka',
                'price': 650,
                'description': 'Spicy marinated tikka chicken chunks, onions, mozzarella, & signature pizza sauce.',
                'image': 'images/pizza.jpg',
                'tag': 'Popular',
                'item_code': 'pizza-tikka',
                'order': 5
            },
            {
                'cat': 'pizzas',
                'name': 'Chicken Fajita Pizza',
                'slug': 'pizza-fajita',
                'price': 680,
                'description': 'Fajita chicken, bell peppers, onions, herbs, and melted mozzarella cheese.',
                'image': 'images/pizza.jpg',
                'tag': '',
                'item_code': 'pizza-fajita',
                'order': 6
            },
            {
                'cat': 'pizzas',
                'name': 'Cheese Margherita Pizza',
                'slug': 'pizza-margherita',
                'price': 520,
                'description': 'Classic Italian tomato sauce, rich extra mozzarella cheese, and fresh oregano.',
                'image': 'images/pizza.jpg',
                'tag': '',
                'item_code': 'pizza-margherita',
                'order': 7
            },

            # Shawarma & Burgers
            {
                'cat': 'shawarma-burgers',
                'name': 'Chicken Shawarma',
                'slug': 'shawarma-chicken',
                'price': 180,
                'description': 'Slow-roasted spiced chicken wrapped in warm pita bread with garlic sauce & pickles.',
                'image': 'images/Menu/Appetizers/Garlic Bread.jpg',
                'tag': 'Local Favorite',
                'item_code': 'shawarma-chicken',
                'custom_style': 'object-fit: cover;',
                'order': 8
            },
            {
                'cat': 'shawarma-burgers',
                'name': 'Crispy Zinger Burger',
                'slug': 'burger-zinger',
                'price': 280,
                'description': 'Hand-breaded crispy fried chicken fillet, mayo, and fresh lettuce in sesame bun.',
                'image': 'images/burger.jpg',
                'tag': 'Crispy',
                'item_code': 'burger-zinger',
                'order': 9
            },
            {
                'cat': 'shawarma-burgers',
                'name': 'Special Beef Burger',
                'slug': 'burger-beef',
                'price': 340,
                'description': 'Juicy grilled beef patty topped with cheese, caramelized onions, & house sauce.',
                'image': 'images/burger.jpg',
                'tag': '',
                'item_code': 'burger-beef',
                'custom_style': 'filter: hue-rotate(45deg);',
                'order': 10
            },

            # Sides & Wings
            {
                'cat': 'sides-wings',
                'name': 'Spicy Hot Wings (6 pcs)',
                'slug': 'wings-hot',
                'price': 320,
                'description': 'Crispy fried chicken wings tossed in signature hot chili sauce.',
                'image': 'images/Menu/Appetizers/Chicken Wings.jpg',
                'tag': 'Spicy',
                'item_code': 'wings-hot',
                'order': 11
            },
            {
                'cat': 'sides-wings',
                'name': 'French Fries (Large)',
                'slug': 'fries-french',
                'price': 180,
                'description': 'Golden crisp potato fries seasoned with secret savory seasoning.',
                'image': 'images/Menu/Appetizers/French Fries.jpg',
                'tag': '',
                'item_code': 'fries-french',
                'order': 12
            },

            # Traditional Pulao
            {
                'cat': 'traditional-pulao',
                'name': 'Special Chicken Pulao',
                'slug': 'pulao-chicken',
                'price': 350,
                'description': 'Aromatic basmati rice cooked in rich chicken stock with tender chicken pieces & spices.',
                'image': 'images/Menu/Main Courses/Alfredo Pasta.jpg',
                'tag': "Chef's Special",
                'item_code': 'pulao-chicken',
                'custom_style': 'filter: saturate(1.2) sepia(0.3);',
                'order': 13
            },
            {
                'cat': 'traditional-pulao',
                'name': 'Special Kabab Pulao',
                'slug': 'pulao-kabab',
                'price': 390,
                'description': 'Traditional spiced rice served with grilled seekh kababs and fresh salad.',
                'image': 'images/Menu/Main Courses/Beef Steak.jpg',
                'tag': '',
                'item_code': 'pulao-kabab',
                'custom_style': 'filter: saturate(0.8) hue-rotate(15deg);',
                'order': 14
            },

            # Beverages
            {
                'cat': 'beverages',
                'name': 'Soft Drinks (500ml)',
                'slug': 'drink-soda',
                'price': 80,
                'description': 'Chilled Coca-Cola, Sprite, or Fanta bottle.',
                'image': 'images/Menu/Bevrages/soft drinks.jpg',
                'tag': '',
                'item_code': 'drink-soda',
                'order': 15
            },
            {
                'cat': 'beverages',
                'name': 'Fresh Lime Soda',
                'slug': 'lime-soda',
                'price': 120,
                'description': 'Refreshing freshly squeezed lemon soda with mint & salt.',
                'image': 'images/Menu/Bevrages/fresh juice.jpg',
                'tag': '',
                'item_code': 'lime-soda',
                'custom_style': 'filter: hue-rotate(90deg) saturate(1.3);',
                'order': 16
            },
        ]

        for pdata in products_data:
            Product.objects.update_or_create(
                slug=pdata['slug'],
                defaults={
                    'category': cat_objs[pdata['cat']],
                    'name': pdata['name'],
                    'price': pdata['price'],
                    'description': pdata['description'],
                    'image': pdata['image'],
                    'tag': pdata.get('tag', ''),
                    'item_code': pdata['item_code'],
                    'custom_style': pdata.get('custom_style', ''),
                    'is_available': True,
                    'display_order': pdata['order']
                }
            )
        self.stdout.write(self.style.SUCCESS('[OK] Products created/updated'))

        # 5. Reviews
        reviews_data = [
            {
                'customer_name': 'Zainab Khan',
                'reviewer_role': 'Regular Diner',
                'rating': 5,
                'comment': '"The best Zinger burgers in Jamrud by far! Always hot, crispy, and cooked fresh. Their WhatsApp pre-ordering saves so much time."',
                'avatar_url': 'https://i.pravatar.cc/120?img=33',
                'order': 1
            },
            {
                'customer_name': 'Hamza Afridi',
                'reviewer_role': 'Local Guide',
                'rating': 5,
                'comment': '"Authentic local shawarma and amazing wood-fired pizzas. Great atmosphere and friendly staff. 5 stars rating well earned!"',
                'avatar_url': 'https://i.pravatar.cc/120?img=12',
                'order': 2
            },
            {
                'customer_name': 'Muhammad Ali',
                'reviewer_role': 'Food Enthusiast',
                'rating': 5,
                'comment': '"Their Special Chicken Pulao is unbeatable in flavor. Family deal pricing is extremely reasonable for the quality provided."',
                'avatar_url': 'https://i.pravatar.cc/120?img=68',
                'order': 3
            },
        ]

        for rdata in reviews_data:
            Review.objects.update_or_create(
                customer_name=rdata['customer_name'],
                defaults={
                    'reviewer_role': rdata['reviewer_role'],
                    'rating': rdata['rating'],
                    'comment': rdata['comment'],
                    'avatar_url': rdata['avatar_url'],
                    'is_approved': True,
                    'display_order': rdata['order']
                }
            )
        self.stdout.write(self.style.SUCCESS('[OK] Reviews created/updated'))
        self.stdout.write(self.style.SUCCESS('Seeding complete! All data successfully loaded.'))
