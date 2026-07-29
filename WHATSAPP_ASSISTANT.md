# 📱 WhatsApp AI Assistant — Architecture & Technical Documentation

## Executive Overview

The **WhatsApp AI Assistant** is a production-ready secondary interface integrated directly into the **Amazing Foods** Django project (`Restaurant_Website`). 

It provides an automated ordering experience via WhatsApp while sharing the exact same Django backend, PostgreSQL database, and business models (`Category`, `Product`, `Deal`, `Order`, `OrderItem`, `OrderNotification`, `RestaurantInfo`) used by the public website and owner dashboard.

---

## 🏛️ Overall Architecture & Data Flow

```
Meta Cloud API Webhook (POST /whatsapp/webhook/)
                     │
                     ▼
       1. HMAC SHA-256 Signature Validation
                     │
                     ▼
  2. Idempotency Check (WhatsAppMessage.message_id)
                     │
                     ▼
    3. Retrieve/Create WhatsAppCustomer & State
                     │
                     ▼
4. Process Message in WhatsAppStateMachine
   - Natural Quantity Parsing ("3 Zingers", "Zinger x3")
   - Cart Editing & Deletion ("remove fries")
   - Order Type Selection (Delivery 🛵 vs Pickup 🛍️)
   - Kitchen Special Instructions
   - Pre-Checkout Live Stock & Price Revalidation
                     │
                     ▼
5. Execute Transactional Order Creation (transaction.atomic())
   - Writes directly to core Order & OrderItem tables
   - Triggers OrderNotification (Owner Dashboard Audio Bell Alert & Unread Badge)
                     │
                     ▼
 6. Send Outbound Response via Meta Graph API v20.0
```

---

## 🔄 Conversation Flow & State Diagram

```
                 [ANY STATE] ──► ("cancel" / "reset" / "menu") ──► [IDLE]
                                       │
                                       ▼
                                 [1. IDLE State]
                   (Types "hi" / "hello" / "start" / any msg)
                                       │
                                       ▼
                             [2. MAIN_MENU State]
       Shows: 0. 🔥 Special Deals | 1. Pizzas | 2. Burgers | 3. Beverages...
                      │                                 │
     (Selects '0' or "deals")                  (Selects '1' or "pizzas")
                      │                                 │
                      ▼                                 ▼
             [Shows Deals Items]               [Shows Category Items]
                      │                                 │
                      └────────────────┬────────────────┘
                                       │
                                       ▼
                           [3. BUILDING_ORDER State]
                   (Customer types item name or number to add)
                        - Item validated against DB live
                        - Added to customer.draft_cart_data
                        - Asks: "Add more items or type 'checkout'?"
                                       │
                             (Types "checkout")
                                       │
                                       ▼
                         [4. SELECT_ORDER_TYPE State]
               Options: 1. 🛵 Delivery  |  2. 🛍️ Pickup / Takeaway
                                 │                 │
                           (Selects 1)       (Selects 2)
                                 │                 │
                                 ▼                 │
                     [5. AWAITING_ADDRESS State]   │
                      (Inputs Delivery Address)    │
                                 │                 │
                                 └────────┬────────┘
                                          │
                                          ▼
                             [6. AWAITING_NOTES State]
                       (Inputs Kitchen Instructions / Notes)
                                          │
                                          ▼
                            [7. CONFIRMING_ORDER State]
             (Shows full Order Summary: Items, Qty, Total, Address, Notes)
                  Asks: "Reply 'yes' or 'confirm' to place order!"
                                          │
                                 (Types "yes")
                                          │
                          [transaction.atomic() Block]
            1. Re-validates Product Availability & Latest DB Prices
            2. Creates Order (order_notes="Placed via WhatsApp Assistant...")
            3. Creates OrderItems (product, quantity, subtotal)
            4. Creates OrderNotification (triggers live dashboard sound alert!)
            5. Clears customer.draft_cart_data & sets state = IDLE
                                          │
                                          ▼
                            [8. ORDER COMPLETED!]
                  Sends confirmation text with #WA-YYYYMMDD-XXXX
```

---

## 🗄️ Database Relationships & Models

```
┌──────────────────────────┐          1:N         ┌──────────────────────────┐
│     WhatsAppCustomer     │ ───────────────────► │     WhatsAppMessage      │
├──────────────────────────┤                      ├──────────────────────────┤
│ id (PK)                  │                      │ id (PK)                  │
│ phone_number (Unique)    │                      │ message_id (Indexed)     │
│ name                     │                      │ customer (FK)            │
│ default_address          │                      │ direction                │
│ order_type               │                      │ body                     │
│ kitchen_notes            │                      │ status                   │
│ state                    │                      └──────────────────────────┘
│ draft_cart_data (JSON)   │
│ last_interaction         │
└──────────────────────────┘
             │ (Creates Order via transaction.atomic())
             ▼
┌──────────────────────────┐          1:N         ┌──────────────────────────┐
│          Order           │ ───────────────────► │        OrderItem         │
├──────────────────────────┤                      ├──────────────────────────┤
│ id (PK)                  │                      │ id (PK)                  │
│ order_id (Unique)        │                      │ order (FK)               │
│ customer_name            │                      │ product (FK)             │
│ customer_phone           │                      │ product_name             │
│ delivery_address         │                      │ quantity                 │
│ order_notes              │                      │ unit_price               │
│ total_price              │                      │ subtotal                 │
│ order_status             │                      └──────────────────────────┘
└──────────────────────────┘
             │
             │ (Triggers Owner Dashboard Audio Alert)
             ▼
┌──────────────────────────┐
│    OrderNotification     │
├──────────────────────────┤
│ id (PK)                  │
│ order (FK)               │
│ title                    │
│ notification_type        │
│ is_read                  │
└──────────────────────────┘
```

---

## 🔑 Environment Variables Required

Add the following to Railway environment variables:

```env
WHATSAPP_TOKEN=EAAG...                              # Meta Cloud API Access Token
WHATSAPP_PHONE_NUMBER_ID=109283746591823            # Meta Business Phone Number ID
WHATSAPP_VERIFY_TOKEN=amazing_foods_wa_secret_2026  # Webhook Verification Secret
WHATSAPP_APP_SECRET=a8f9c10293...                   # Meta App Secret for HMAC Validation
```

---

## 🚀 Deployment Steps to Railway

1. Commit and push the project changes to GitHub.
2. In Railway Dashboard, add the environment variables listed above.
3. Open Meta for Developers Console (`https://developers.facebook.com/`):
   - Go to **WhatsApp** -> **Configuration**.
   - Set **Callback URL**: `https://your-app-domain.up.railway.app/whatsapp/webhook/`
   - Set **Verify Token**: `amazing_foods_wa_secret_2026`
   - Click **Verify and Save**.
   - Under **Webhook Fields**, subscribe to `messages`.

---

## 🛠️ Troubleshooting Guide

1. **Meta Webhook Verification Fails**:
   - Verify `WHATSAPP_VERIFY_TOKEN` matches the exact string entered in Meta Console.
   - Check Railway deploy logs to confirm `/whatsapp/webhook/` route returns HTTP 200.

2. **Incoming Messages Not Replying**:
   - Check `WhatsAppSetting.objects.first().auto_reply_enabled` is set to `True`.
   - Verify `WHATSAPP_TOKEN` has `whatsapp_business_messaging` permissions in Meta App settings.

3. **Audio Bell Alert Not Playing on Owner Dashboard**:
   - Ensure the browser tab logged into `/owner/dashboard/` has sound enabled.
   - `OrderNotification.objects.create()` will automatically generate an unread notification object which the dashboard polls every 10 seconds.
