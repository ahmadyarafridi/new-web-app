import re
import uuid
import logging
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from website.models import RestaurantInfo, Category, Product, Deal, Order, OrderItem, OrderNotification
from .models import WhatsAppCustomer, WhatsAppSetting
from .services import WhatsAppService

logger = logging.getLogger(__name__)


class WhatsAppStateMachine:
    """
    Production-Hardened Deterministic State Machine for WhatsApp ordering.
    All orders are 100% Delivery orders (Pickup branch completely removed).
    Flow: IDLE -> MAIN_MENU -> BUILDING_ORDER -> AWAITING_ADDRESS -> AWAITING_NOTES -> CONFIRMING_ORDER.
    """

    @classmethod
    def process_incoming(cls, sender_phone: str, sender_name: str, message_text: str, interactive_id: str = None) -> str:
        customer, created = WhatsAppCustomer.objects.get_or_create(
            phone_number=sender_phone,
            defaults={'name': sender_name}
        )

        now = timezone.now()
        is_inactive = (now - customer.last_interaction) > timedelta(minutes=10) if not created else False

        if sender_name and not customer.name:
            customer.name = sender_name

        text = (message_text or '').strip().lower()
        if interactive_id:
            text = interactive_id.lower()

        # Update last interaction timestamp
        customer.save()

        # Global Commands (reset, cancel, restart, clear)
        if text in ['reset', 'cancel', 'clear', 'restart', '0', 'btn_clear_cart', 'btn_cancel_order']:
            customer.clear_draft()
            reply = "Your order draft has been cleared. Type *hi* or *menu* anytime to start a new order! 🍔"
            WhatsAppService.send_text_message(sender_phone, reply)
            return reply

        # Persistent Cart Inactivity Recovery Check
        if is_inactive and customer.draft_cart_data and customer.state not in ['IDLE', 'WELCOME_BACK']:
            customer.state = 'WELCOME_BACK'
            customer.save()
            return cls.handle_welcome_back(customer, text)

        if customer.state == 'WELCOME_BACK':
            return cls.handle_welcome_back(customer, text)

        # Global Cart View & Edit Commands
        if text in ['cart', 'view cart', 'my cart', 'edit cart', 'btn_edit_cart']:
            return cls.handle_edit_cart(customer, text)

        # Route State Machine Logic
        state = customer.state

        if state == 'IDLE' or text in ['hi', 'hello', 'hey', 'menu', 'start', 'help', 'btn_start_fresh']:
            if text == 'btn_start_fresh':
                customer.clear_draft()
            return cls.handle_idle(customer, text)

        elif state == 'MAIN_MENU':
            return cls.handle_main_menu(customer, text, interactive_id)

        elif state == 'BUILDING_ORDER':
            return cls.handle_building_order(customer, text, interactive_id)

        elif state == 'EDIT_CART':
            return cls.handle_edit_cart(customer, text)

        elif state == 'AWAITING_ADDRESS':
            return cls.handle_awaiting_address(customer, text)

        elif state == 'AWAITING_NOTES':
            return cls.handle_awaiting_notes(customer, text)

        elif state == 'CONFIRMING_ORDER':
            return cls.handle_confirming_order(customer, text)

        else:
            return cls.handle_idle(customer, text)

    @classmethod
    def handle_welcome_back(cls, customer, text):
        if text in ['btn_continue_cart', 'continue', 'keep']:
            return cls.handle_edit_cart(customer, 'view')
        elif text in ['btn_start_fresh', 'fresh', 'new', 'reset']:
            customer.clear_draft()
            return cls.handle_idle(customer, 'hi')

        cart = customer.draft_cart_data
        total = sum(item['price'] * item['qty'] for item in cart)
        msg = f"👋 *Welcome Back, {customer.name or 'Customer'}!*\n\nYou still have items in your cart (*Rs. {total:.0f}*):\n"
        for item in cart:
            msg += f"• {item['name']} x{item['qty']}\n"

        msg += "\nWould you like to continue with your previous order or start fresh?"

        buttons = [
            {'id': 'btn_continue_cart', 'title': 'Continue Cart'},
            {'id': 'btn_start_fresh', 'title': 'Start Fresh'}
        ]

        WhatsAppService.send_interactive_buttons(customer.phone_number, msg, buttons)
        WhatsAppService.send_text_message(customer.phone_number, f"{msg}\n\nReply *1* to Continue Cart, or *2* to Start Fresh.")
        return msg

    @classmethod
    def handle_idle(cls, customer, text):
        categories = list(Category.objects.all().order_by('display_order', 'id'))

        header = "AMAZING FOODS MENU"
        body = f"Welcome to *Amazing Foods*! 🍔✨\n\nPlease select a category to browse our menu:"

        sections = [
            {
                "title": "Categories",
                "rows": [{"id": "cat_deals", "title": "🔥 Special Deals", "description": "Combo packages & savings"}] + [
                    {"id": f"cat_{cat.id}", "title": f"🍽️ {cat.name[:20]}", "description": f"Browse {cat.name}"}
                    for cat in categories
                ]
            }
        ]

        WhatsAppService.send_interactive_list(customer.phone_number, header, body, "View Categories", sections)

        fallback = f"Welcome to *Amazing Foods*! 🍔✨\n\n*OUR MENU CATEGORIES:*\n0. 🔥 Special Deals\n"
        for idx, cat in enumerate(categories, start=1):
            fallback += f"{idx}. {cat.name}\n"
        fallback += "\n*Reply with category number or name to view items!*"

        customer.state = 'MAIN_MENU'
        customer.save()

        WhatsAppService.send_text_message(customer.phone_number, fallback)
        return fallback

    @classmethod
    def handle_main_menu(cls, customer, text, interactive_id):
        categories = list(Category.objects.all().order_by('display_order', 'id'))
        deals = list(Deal.objects.filter(is_active=True).order_by('-id'))

        if text in ['0', 'cat_deals', 'deals', 'special deals', 'deal']:
            if not deals:
                msg = f"No active deals right now! Please pick a category from 1 to {len(categories)}."
                WhatsAppService.send_text_message(customer.phone_number, msg)
                return msg

            msg = "🔥 *SPECIAL DEALS* 🔥\n\n"
            for d in deals:
                msg += f"• *{d.title}* - Rs. {d.discount_price:.0f}\n_{d.description}_\n\n"
            msg += "Reply with item name or quantity (e.g. '2 deals') to add to cart, or type 'menu'."
            customer.state = 'BUILDING_ORDER'
            customer.save()
            WhatsAppService.send_text_message(customer.phone_number, msg)
            return msg

        cat_obj = None
        if interactive_id and interactive_id.startswith('cat_'):
            try:
                cid = int(interactive_id.replace('cat_', ''))
                cat_obj = Category.objects.filter(id=cid).first()
            except ValueError:
                pass

        if not cat_obj:
            try:
                cat_idx = int(text) - 1
                if 0 <= cat_idx < len(categories):
                    cat_obj = categories[cat_idx]
            except ValueError:
                for c in categories:
                    if c.name.lower() in text or text in c.name.lower():
                        cat_obj = c
                        break

        if not cat_obj:
            reply = f"Please reply with a valid category number (1 to {len(categories)}) or type 'menu'."
            WhatsAppService.send_text_message(customer.phone_number, reply)
            return reply

        products = list(Product.objects.filter(category=cat_obj, is_available=True).order_by('-id'))
        if not products:
            reply = f"No items currently available in *{cat_obj.name}*. Please pick another category!"
            WhatsAppService.send_text_message(customer.phone_number, reply)
            return reply

        items_text = f"🍽️ *{cat_obj.name.upper()} MENU*\n\n"
        for idx, p in enumerate(products, start=1):
            items_text += f"{idx}. *{p.name}* - Rs. {p.price:.0f}\n"
            if p.description:
                items_text += f"   _{p.description[:50]}_\n"

        items_text += "\n*Reply with item name or quantity (e.g. '3 Zinger Burgers' or 'Zinger x3'), or type 'checkout' when ready!*"

        customer.state = 'BUILDING_ORDER'
        customer.selected_category_id = cat_obj.id
        customer.save()

        WhatsAppService.send_text_message(customer.phone_number, items_text)
        return items_text

    @classmethod
    def handle_building_order(cls, customer, text, interactive_id):
        rest_info = RestaurantInfo.objects.first()
        if rest_info and hasattr(rest_info, 'is_open') and not rest_info.is_open:
            msg = "ℹ️ *Ordering Unavailable*: Amazing Foods is currently CLOSED for ordering. You can still browse our menu! Opening hours will resume soon."
            WhatsAppService.send_text_message(customer.phone_number, msg)
            return msg

        if text in ['checkout', 'done', 'cart', 'order', 'pay', 'btn_checkout']:
            cart_data = customer.draft_cart_data
            if not cart_data:
                reply = "Your cart is empty! Please select an item or type 'menu'."
                WhatsAppService.send_text_message(customer.phone_number, reply)
                return reply

            customer.state = 'AWAITING_ADDRESS'
            customer.save()

            saved_addr = customer.default_address or ""
            prompt = "🛵 *DELIVERY ORDER*\n\nPlease enter your *Delivery Address* (Street, House #, Area):"
            if saved_addr:
                prompt += f"\n\nOr reply *'1'* to use previous address: _{saved_addr}_"

            WhatsAppService.send_text_message(customer.phone_number, prompt)
            return prompt

        qty, item_query = cls._parse_quantity_and_name(text)

        matched_product = None
        products = list(Product.objects.filter(is_available=True))

        if customer.selected_category_id:
            cat_products = list(Product.objects.filter(category_id=customer.selected_category_id, is_available=True).order_by('-id'))
            try:
                item_idx = int(item_query) - 1
                if 0 <= item_idx < len(cat_products):
                    matched_product = cat_products[item_idx]
            except ValueError:
                pass

        if not matched_product:
            for p in products:
                if p.name.lower() in item_query or item_query in p.name.lower():
                    matched_product = p
                    break

        if not matched_product:
            matched_deal = None
            for d in Deal.objects.filter(is_active=True):
                if d.title.lower() in item_query or item_query in d.title.lower():
                    matched_deal = d
                    break

            if matched_deal:
                cart = customer.draft_cart_data
                cart.append({
                    'product_id': None,
                    'name': matched_deal.title,
                    'price': float(matched_deal.discount_price),
                    'qty': qty
                })
                customer.draft_cart_data = cart
                customer.save()

                total = sum(item['price'] * item['qty'] for item in cart)
                reply = f"✅ Added *{matched_deal.title} x{qty}* (Rs. {matched_deal.discount_price * qty:.0f}) to cart!\n\n*Cart Total: Rs. {total:.0f}*\n\nReply with another item name, or type *'checkout'* to complete order!"
                WhatsAppService.send_text_message(customer.phone_number, reply)
                return reply

            reply = "Item not found or unavailable. Type exact item name (e.g. '3 Zingers') or 'checkout'."
            WhatsAppService.send_text_message(customer.phone_number, reply)
            return reply

        cart = customer.draft_cart_data
        existing = next((item for item in cart if item.get('product_id') == matched_product.id), None)
        if existing:
            existing['qty'] = min(20, existing['qty'] + qty)
        else:
            cart.append({
                'product_id': matched_product.id,
                'name': matched_product.name,
                'price': float(matched_product.price),
                'qty': qty
            })

        customer.draft_cart_data = cart
        customer.save()

        total = sum(item['price'] * item['qty'] for item in cart)
        msg = f"✅ Added *{matched_product.name} x{qty}* (Rs. {matched_product.price * qty:.0f}) to cart!\n\n*Cart Total: Rs. {total:.0f}*\n\nType another item, *'cart'* to edit, or *'checkout'* to finish!"
        WhatsAppService.send_text_message(customer.phone_number, msg)
        return msg

    @classmethod
    def handle_edit_cart(cls, customer, text):
        cart = customer.draft_cart_data
        text_clean = text.lower().strip()

        if text_clean.startswith(('remove', 'delete', 'drop')):
            query = re.sub(r'^(remove|delete|drop)\s*', '', text_clean).strip()
            if query:
                try:
                    del_idx = int(query) - 1
                    if 0 <= del_idx < len(cart):
                        removed = cart.pop(del_idx)
                        customer.draft_cart_data = cart
                        customer.save()
                        msg = f"🗑️ Removed *{removed['name']}* from cart."
                        WhatsAppService.send_text_message(customer.phone_number, msg)
                except ValueError:
                    new_cart = [item for item in cart if query not in item['name'].lower()]
                    if len(new_cart) < len(cart):
                        customer.draft_cart_data = new_cart
                        customer.save()
                        cart = new_cart
                        msg = f"🗑️ Removed *{query}* from cart."
                        WhatsAppService.send_text_message(customer.phone_number, msg)

        customer.state = 'EDIT_CART'
        customer.save()

        if not cart:
            msg = "🛒 Your cart is currently empty! Type *'menu'* to browse items."
            customer.state = 'IDLE'
            customer.save()
            WhatsAppService.send_text_message(customer.phone_number, msg)
            return msg

        cart_msg = "🛒 *YOUR CART SUMMARY:*\n\n"
        total = 0
        for idx, item in enumerate(cart, start=1):
            sub = item['price'] * item['qty']
            total += sub
            cart_msg += f"{idx}. *{item['name']}* x{item['qty']} = Rs. {sub:.0f}\n"

        cart_msg += f"\n💰 *TOTAL:* Rs. {total:.0f}\n\n"
        cart_msg += "To edit: type *'remove 1'* to delete an item, or type *'checkout'* to complete order!"

        buttons = [
            {'id': 'btn_checkout', 'title': 'Checkout'},
            {'id': 'btn_clear_cart', 'title': 'Clear Cart'}
        ]

        WhatsAppService.send_interactive_buttons(customer.phone_number, cart_msg, buttons)
        WhatsAppService.send_text_message(customer.phone_number, cart_msg)
        return cart_msg

    @classmethod
    def handle_awaiting_address(cls, customer, text):
        if text == '1' and customer.default_address:
            address = customer.default_address
        else:
            address = text
            customer.default_address = address

        customer.state = 'AWAITING_NOTES'
        customer.save()

        prompt = "📍 Address saved!\n\nAny special instructions for the kitchen? (e.g. 'No onions, extra spicy') or reply *'none'* to skip."
        WhatsAppService.send_text_message(customer.phone_number, prompt)
        return prompt

    @classmethod
    def handle_awaiting_notes(cls, customer, text):
        if text in ['none', 'no', 'skip', '-']:
            customer.kitchen_notes = ""
        else:
            customer.kitchen_notes = text

        customer.state = 'CONFIRMING_ORDER'
        customer.save()

        cart = customer.draft_cart_data
        subtotal = sum(item['price'] * item['qty'] for item in cart)
        total = subtotal

        config = WhatsAppSetting.objects.first()
        prep_time = config.estimated_prep_time if config else "25 - 35 mins"

        summary = "📋 *PRE-ORDER SUMMARY & CONFIRMATION*\n\n"
        summary += "Type: *Delivery Order 🛵*\n"
        summary += f"⏱️ *Est. Delivery Time:* {prep_time}\n\n"
        summary += "*ITEMS:*\n"
        for item in cart:
            sub = item['price'] * item['qty']
            summary += f"• {item['name']} x{item['qty']} @ Rs. {item['price']:.0f} = Rs. {sub:.0f}\n"

        summary += f"\n💵 *SUBTOTAL:* Rs. {subtotal:.0f}\n"
        summary += f"💰 *TOTAL AMOUNT:* Rs. {total:.0f}\n"
        summary += f"📍 *DELIVERY ADDRESS:* {customer.default_address}\n"
        if customer.kitchen_notes:
            summary += f"📝 *KITCHEN NOTES:* {customer.kitchen_notes}\n"

        summary += "\nReply *'yes'* or tap *Confirm Order* to place your order now!"

        buttons = [
            {'id': 'btn_confirm_order', 'title': 'Confirm Order'},
            {'id': 'btn_edit_cart', 'title': 'Edit Cart'},
            {'id': 'btn_cancel_order', 'title': 'Cancel'}
        ]

        WhatsAppService.send_interactive_buttons(customer.phone_number, summary, buttons)
        WhatsAppService.send_text_message(customer.phone_number, summary)
        return summary

    @classmethod
    def handle_confirming_order(cls, customer, text):
        if text in ['yes', 'confirm', 'ok', 'sure', '1', 'btn_confirm_order']:
            return cls.create_whatsapp_order(customer)

        reply = "Please reply *'yes'* or tap *Confirm Order* to place your order, or *'edit'* to modify items."
        WhatsAppService.send_text_message(customer.phone_number, reply)
        return reply

    @classmethod
    def create_whatsapp_order(cls, customer):
        rest_info = RestaurantInfo.objects.first()
        if rest_info and hasattr(rest_info, 'is_open') and not rest_info.is_open:
            msg = "ℹ️ *Ordering Unavailable*: Amazing Foods is currently CLOSED for ordering. Your cart is saved!"
            WhatsAppService.send_text_message(customer.phone_number, msg)
            return msg

        cart = customer.draft_cart_data
        if not cart:
            customer.clear_draft()
            reply = "Your cart was empty. Type 'menu' to start again!"
            WhatsAppService.send_text_message(customer.phone_number, reply)
            return reply

        try:
            with transaction.atomic():
                revalidated_cart = []
                unavailable_items = []
                price_changes = []
                total_price = 0

                for item in cart:
                    prod_id = item.get('product_id')
                    if prod_id:
                        prod = Product.objects.filter(id=prod_id).first()
                        if not prod or not prod.is_available:
                            unavailable_items.append(item['name'])
                            continue

                        live_price = float(prod.price)
                        if abs(live_price - float(item['price'])) > 0.01:
                            price_changes.append(f"• *{prod.name}*: WAS Rs. {item['price']:.0f} ➔ NOW Rs. {live_price:.0f}")

                        revalidated_cart.append({
                            'product_id': prod.id,
                            'name': prod.name,
                            'price': live_price,
                            'qty': item['qty']
                        })
                        total_price += live_price * item['qty']
                    else:
                        deal = Deal.objects.filter(title__iexact=item['name'], is_active=True).first()
                        if not deal:
                            unavailable_items.append(item['name'])
                            continue

                        live_price = float(deal.discount_price)
                        if abs(live_price - float(item['price'])) > 0.01:
                            price_changes.append(f"• *{deal.title}*: WAS Rs. {item['price']:.0f} ➔ NOW Rs. {live_price:.0f}")

                        revalidated_cart.append({
                            'product_id': None,
                            'name': deal.title,
                            'price': live_price,
                            'qty': item['qty']
                        })
                        total_price += live_price * item['qty']

                if unavailable_items:
                    customer.draft_cart_data = revalidated_cart
                    customer.state = 'EDIT_CART'
                    customer.save()

                    alert_msg = f"⚠️ *ITEM UNAVAILABLE NOTICE*\n\nThe following item(s) are currently out of stock:\n"
                    for un_item in unavailable_items:
                        alert_msg += f"• *{un_item}*\n"
                    alert_msg += "\nThey have been removed from your cart. Please review your cart below:"

                    buttons = [
                        {'id': 'btn_remove_unavailable', 'title': 'Review Cart'},
                        {'id': 'btn_cancel_order', 'title': 'Cancel Order'}
                    ]
                    WhatsAppService.send_interactive_buttons(customer.phone_number, alert_msg, buttons)
                    WhatsAppService.send_text_message(customer.phone_number, alert_msg)
                    return cls.handle_edit_cart(customer, 'view')

                if price_changes:
                    customer.draft_cart_data = revalidated_cart
                    customer.state = 'EDIT_CART'
                    customer.save()

                    price_msg = f"⚠️ *MENU PRICE UPDATE NOTICE*\n\nThe price of the following item(s) was updated in our menu:\n"
                    for p_change in price_changes:
                        price_msg += f"{p_change}\n"
                    price_msg += f"\n💰 *Updated Cart Total: Rs. {total_price:.0f}*\n\nPlease review your updated cart below and confirm:"

                    buttons = [
                        {'id': 'btn_checkout', 'title': 'Proceed to Checkout'},
                        {'id': 'btn_clear_cart', 'title': 'Clear Cart'}
                    ]
                    WhatsAppService.send_interactive_buttons(customer.phone_number, price_msg, buttons)
                    WhatsAppService.send_text_message(customer.phone_number, price_msg)
                    return cls.handle_edit_cart(customer, 'view')

                notes = "Placed via WhatsApp Assistant (Delivery 🛵)"
                if customer.kitchen_notes:
                    notes += f" | Kitchen Notes: {customer.kitchen_notes}"

                order_id = f"WA-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

                order = Order.objects.create(
                    order_id=order_id,
                    customer_name=customer.name or f"WhatsApp Customer ({customer.phone_number[-4:]})",
                    customer_phone=customer.phone_number,
                    delivery_address=customer.default_address or "Delivery",
                    order_notes=notes,
                    total_price=total_price,
                    order_status='pending',
                    payment_status='unpaid'
                )

                for item in revalidated_cart:
                    prod_id = item.get('product_id')
                    prod_obj = Product.objects.filter(id=prod_id).first() if prod_id else None
                    OrderItem.objects.create(
                        order=order,
                        product=prod_obj,
                        product_name=item['name'],
                        quantity=item['qty'],
                        unit_price=item['price'],
                        subtotal=item['price'] * item['qty']
                    )

                OrderNotification.objects.create(
                    order=order,
                    title=f"New WhatsApp Order #{order.order_id}",
                    message=f"{order.customer_name} placed a Delivery order of Rs. {total_price:.0f}.",
                    customer_name=order.customer_name,
                    total_price=total_price,
                    notification_type='new_order',
                    is_read=False
                )

                customer.clear_draft()

            config = WhatsAppSetting.objects.first()
            prep_time = config.estimated_prep_time if config else "25 - 35 mins"

            confirmation_text = "🎉 *ORDER PLACED SUCCESSFULLY!*\n\n"
            confirmation_text += f"🆔 *Order ID:* #{order.order_id}\n"
            confirmation_text += "Type: *Delivery Order 🛵*\n"
            confirmation_text += f"⏱️ *Est. Delivery Time:* {prep_time}\n"
            confirmation_text += f"💰 *Total Price:* Rs. {total_price:.0f}\n"
            confirmation_text += "⏳ *Status:* Pending Approval\n\n"
            confirmation_text += "Our kitchen will start preparing your order shortly! You will receive live status updates right here on WhatsApp. Thank you for choosing Amazing Foods! 🍔❤️"

            WhatsAppService.send_text_message(customer.phone_number, confirmation_text)
            logger.info(f"[WhatsApp Order] Order #{order.order_id} created for {customer.phone_number}")
            return confirmation_text

        except Exception as e:
            logger.error(f"[WhatsApp Order Error] Transaction failed for {customer.phone_number}: {e}")
            error_text = "An error occurred while placing your order. Please try again or call us directly."
            WhatsAppService.send_text_message(customer.phone_number, error_text)
            return error_text

    @classmethod
    def _parse_quantity_and_name(cls, text: str):
        text = text.strip()
        m1 = re.match(r'^(\d+)\s*(?:x|\*|\s)?\s+(.+)$', text, re.IGNORECASE)
        if m1:
            try:
                qty = int(m1.group(1))
                name = m1.group(2).strip()
                return min(20, max(1, qty)), name
            except ValueError:
                pass

        m2 = re.match(r'^(.+?)\s+(?:x|\*|\s)?\s*(\d+)$', text, re.IGNORECASE)
        if m2:
            try:
                name = m2.group(1).strip()
                qty = int(m2.group(2))
                return min(20, max(1, qty)), name
            except ValueError:
                pass

        return 1, text
