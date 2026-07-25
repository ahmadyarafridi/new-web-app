# 🍔 Delicious Food Stop — Django Web Application

[![Django](https://img.shields.io/badge/Django-6.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)

A production-ready full-stack Django web application built for **Delicious Food Stop**, a popular fast-food restaurant based in Jamrud, Khyber Pakhtunkhwa. Designed with a luxury dark & gold aesthetic, seamless page transitions, interactive menu filtering, direct WhatsApp ordering, and restaurant owner authentication.

---

## ✨ Features

- 📱 **Fully Responsive Layout**: Custom tailored experiences across Desktop, Laptop, Tablet, and Mobile screens.
- 🐍 **Modular Django Architecture**: Clean app separation (`website` for public pages, `accounts` for owner authentication).
- 🔐 **Owner Authentication & Dashboard**: Protected owner login/logout portal (`/owner/login/`) redirecting to a placeholder dashboard.
- 🛒 **Persistent Shopping Cart**: Pre-order items saved seamlessly in browser `localStorage`.
- 💬 **Direct WhatsApp Checkout**: 1-Click order confirmation that automatically pre-fills item details, quantities, and totals into WhatsApp.
- 🍕 **Interactive Food Menu**: Instant keyword search and custom category filters for pizzas, burgers, shawarmas, appetizers, beverages, and desserts.
- 🎨 **Luxury Dark Theme**: Custom CSS design system with HSL gold accents, smooth hover micro-interactions, and 60fps animations.
- 📍 **Location & Operational Hours**: Embedded Google Maps location (Jamrud), contact channels, and live status badge.

---

## 📁 Project Structure

```text
Restaurant_Website/
├── manage.py                # Django CLI management script
├── db.sqlite3               # SQLite Database (Development)
├── restaurant_config/       # Django Project Package
│   ├── settings.py          # App settings, static files, template DIRS
│   ├── urls.py              # Root URL router
│   ├── wsgi.py
│   └── asgi.py
├── website/                 # App: Customer-Facing Website (Index, Menu, About, Contact)
├── accounts/                # App: Owner Authentication (Login, Logout, Dashboard)
├── static/                  # Centralized Static Assets (CSS, JS, Images)
└── templates/               # Django Master & App Templates
    ├── base.html            # Master layout with DTL loads
    ├── website/             # Public page templates
    └── accounts/            # Owner portal templates
```

---

## 🚀 Getting Started

### Local Setup & Execution

1. **Clone the repository**:
   ```bash
   git clone https://github.com/harisyar-ai/restaurant-web-app.git
   cd restaurant-web-app
   ```

2. **Apply database migrations**:
   ```bash
   python manage.py migrate
   ```

3. **Start the Django development server**:
   ```bash
   python manage.py runserver
   ```

4. **Access the application**:
   - Customer Website: `http://127.0.0.1:8000/`
   - Owner Login Portal: `http://127.0.0.1:8000/owner/login/`
     - **Default Owner Username**: `admin`
     - **Default Owner Password**: `admin123`

---

## 🛠️ Built With

- **Backend**: Django 6.0+ (Python)
- **Database**: SQLite3 (Development)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Fonts & Icons**: Google Fonts (*Cinzel*, *Playfair Display*, *Plus Jakarta Sans*), FontAwesome 6

---

## 📄 License & Credits

Developed by **Muhammad Haris Afridi** for **Delicious Food Stop**. All rights reserved.
