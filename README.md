# 🚗🌍 AssetLinkAfrica
## Real Estate & Automotive Leasing Platform
AssetLinkAfrica is a modern digital platform designed to connect users with cars and land listings for lease or purchase. The platform combines real estate and automotive marketplaces into one seamless experience.

# 📌 Project Overview
This project is built using a frontend-first approach, later integrated into a Django backend for scalability, security, and dynamic functionality.

# 🏗️ Project Structure
## 🔹Frontend (Static)

frontend/
├── assets/        # Images, logos, icons
├── css/           # Stylesheets (main.css, responsive.css)
├── js/            # JavaScript files for interactivity – navbar, form validation, etc.
├── templates/     # HTML templates (for Django integration)
│   ├── index.html (Homepage – landing page with search functionality)
│   ├── listings.html(Page to display available cars & land for lease)
│   ├── details.html(Individual listing details page)
│   ├── login.html(User authentication page – login/register)
│   ├── dashboard.html(User profile – manage listings & bookings)
│   ├── admin.html(Admin panel for verification, user management, etc.)
├── base.html (Main layout – navbar, footer, etc.)
└── README.md

## 🔹 Backend (Django)
📂 backend/
├── 📂 flex_leasing/ (Main Django project folder)
│ ├── 📂 core/ (Main app – authentication, models, views)
│ ├── 📂 listings/ (App for managing car & land listings)
│ ├── 📂 bookings/ (App for lease transactions, payments, etc.)
│ ├── 📂 templates/ (Will later replace static HTML files when integrated)
│ ├── 📂 static/ (Where frontend assets will be stored for Django templates)
│ ├── 📜 settings.py (Project settings – database, authentication, static files)
│ ├── 📜 urls.py (Routes for handling different pages and API endpoints)
│ ├── 📜 views.py (Handles business logic – fetching listings, user authentication)
│ ├── 📜 models.py (Database schema – Users, Listings, Bookings, Payments)
│ ├── 📜 admin.py (Admin panel for managing users, listings, payments)
│ ├── 📜 manage.py (Main entry point for Django commands)
│
├── 📂 venv/ (Virtual environment for dependencies)
├── 📜 requirements.txt (Django, PostgreSQL, Pillow for images, etc.)
├── 📜 .env (Environment variables for security keys, database URL
└── 📜 Dockerfile (Optional – for containerized deployment)

## ⚙️ Tech Stack
Frontend
HTML5
CSS3 / TailwindCSS (optional)
JavaScript (Vanilla)
Backend
Python
Django
PostgreSQL
Django REST Framework (optional for APIs)
DevOps (Optional)
Docker
Environment Variables (.env)

## 🚀 Development Plan
🟢 Phase 1: Frontend
Build landing page (search + branding)
Create listings UI (cars & land)
Design dashboard & authentication pages
Ensure responsive design (mobile-first)

🟡 Phase 2: Backend (Django)
Initialize Django project
Configure PostgreSQL database
Create models:
Users
Listings
Bookings
Payments
Implement authentication system
Build APIs for listings & bookings

🔵 Phase 3: Integration
Convert HTML → Django templates
Use {% extends %} and {% include %}
Configure static files handling
Implement:
Search & filtering
User dashboard functionality
Listing management (CRUD)
🔐 Key Features
🔍 Advanced search (cars & land)
👤 User authentication (login/register)
📊 User dashboard (manage listings & bookings)
🏷️ Listing management (add/edit/delete)
💳 Booking & payment system
🛡️ Admin panel for verification & moderation
🛠️ Installation & Setup

## 1. Clone Repository
Bash
git clone https://github.com/bonyborn/AssetLinkAfrica.git
cd AssetLinkAfrica
## 2. Setup Virtual Environment
Bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
## 3. Install Dependencies
Bash
pip install -r requirements.txt
## 4. Configure Environment Variables
Copy `.env.example` to `.env`, then fill in the values for the payment methods you intend to offer. Keep `.env` private and never commit real credentials or bank account details.

```env
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=your_postgresql_url
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-full-gmail-address
EMAIL_HOST_PASSWORD=your-google-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=your-full-gmail-address
TERMII_API_KEY=your-termii-api-key
TERMII_API_BASE_URL=https://api.ng.termii.com
TERMII_SENDER_ID=your-approved-sender-id
MPESA_API_BASE_URL=https://sandbox.safaricom.co.ke
MPESA_CONSUMER_KEY=your-daraja-consumer-key
MPESA_CONSUMER_SECRET=your-daraja-consumer-secret
MPESA_SHORTCODE=your-daraja-shortcode
MPESA_PASSKEY=your-daraja-passkey
MPESA_CALLBACK_URL=https://your-public-domain.example/payments/mpesa/callback/
MPESA_TRANSACTION_TYPE=CustomerPayBillOnline
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-stripe-webhook-secret
BANK_TRANSFER_BANK_NAME=Your bank
BANK_TRANSFER_ACCOUNT_NAME=Your business account name
BANK_TRANSFER_ACCOUNT_NUMBER=Your account number
BANK_TRANSFER_BRANCH=Your branch
BANK_TRANSFER_SWIFT_CODE=Your SWIFT code
BANK_TRANSFER_INSTRUCTIONS=Include your username in the transfer description
```

The payment variables are documented in the standalone `.env.example`. Leave a payment method's values blank until its provider or recipient details are ready; bank transfer is enabled only when its bank name, account name, and account number are configured.

For Gmail, enable 2-Step Verification and create an App Password; use that App Password as `EMAIL_HOST_PASSWORD` (not your regular Google password). Keep `.env` out of source control. If SMTP user/password are absent, the app uses Django's console backend and prints the verification email in the server terminal rather than delivering it.

For SMS verification, create a Termii account and use the API key, base URL, and an approved sender ID from its dashboard. Termii's published API collection uses `https://api.ng.termii.com`; use the base URL shown for your account if it differs. New registrations remain inactive until they verify both the six-digit email code and the six-digit SMS code. Codes expire after 10 minutes, allow five incorrect attempts, and can be resent no more than once per minute.

Users can start password recovery from the login page. Reset links are sent by email only for active accounts, and Django's password-reset token timeout applies; a link cannot be reused after the password changes.

For M-Pesa checkout, create a Safaricom Daraja app and set its consumer key, consumer secret, shortcode, and passkey in `.env`. Use the sandbox API URL for testing and the production URL only after Safaricom approves the app. `MPESA_CALLBACK_URL` must be the public HTTPS URL for `/payments/mpesa/callback/`; bookings remain pending until Safaricom's callback confirms the matching amount, phone number, and receipt. Never request or store an M-Pesa PIN.

Paid listing plans are available at `/payments/subscriptions/`. M-Pesa subscriptions use a Daraja STK Push and activate only after a matching successful callback. Card subscriptions use Stripe-hosted Checkout; configure `STRIPE_SECRET_KEY` and add `https://your-domain/payments/stripe/webhook/` as a Stripe webhook endpoint with the `checkout.session.completed`, `checkout.session.expired`, and `checkout.session.async_payment_failed` events. Store the endpoint signing secret in `STRIPE_WEBHOOK_SECRET`. The app accepts only signed events matching its stored session, plan, user, amount, and KES currency.

Bank subscriptions remain pending until a staff member verifies the transfer in Django admin under **Subscription payments** using the **Verify selected bank transfers** action. Configure the `BANK_TRANSFER_*` recipient settings before accepting transfers. Use test/sandbox credentials during development and never commit `.env` or provider secrets. Paid plan purchases activate one month at a time and do not auto-renew; users must make another payment to renew.
## 5. Run Migrations
Bash
python manage.py migrate
## 6. Start Server
Bash
python manage.py runserver
## 📱 Future Improvements
Mobile app (React Native / Flutter)
AI-based recommendations
Map integration for land locations
Real-time chat between buyers & sellers
## 🤝 Contribution
Contributions are welcome!
Fork the repo and submit a pull request.
##📄 License
MIT License
