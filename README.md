<div align="center">

# 📚 Smart Library Management System

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=3000&pause=1000&color=10B981&center=true&vCenter=true&width=600&lines=Smart+Library+System;Manage+%7C+Borrow+%7C+Learn;Built+with+Django+6" alt="Typing SVG" />

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Local-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![License](https://img.shields.io/badge/License-Educational-10B981?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

<br/>

> **A full-featured, role-based Library Management System** built with Django 6 — covering everything from book borrowing and fine payments to analytics, PDF reading, email notifications, and data exports. Designed for local deployment with PostgreSQL.

<br/>


```
╔══════════════════════════════════════════════════════════════╗
║          📚  Smart Library Management System                 ║
║   Student · Librarian · Admin  —  All roles. One platform.  ║
╚══════════════════════════════════════════════════════════════╝
```



</div>

---

## 📑 Table of Contents

- [✨ Overview](#-overview)
- [🏗️ Tech Stack](#️-tech-stack)
- [🗂️ Project Structure](#️-project-structure)
- [🚀 Quick Start](#-quick-start)
- [🎓 Student Features](#-student-features)
- [📚 Librarian Features](#-librarian-features)
- [🛡️ Admin Features](#️-admin-features)
- [🔐 Authentication & Security](#-authentication--security)
- [📧 Email Notifications](#-email-notifications)
- [💳 Payment System](#-payment-system)
- [🔌 REST API](#-rest-api)
- [⚙️ Configuration](#️-configuration)
- [🗄️ Data Models](#️-data-models)
- [🔧 Management Commands](#-management-commands)

---

## ✨ Overview

Smart Library Management System is a comprehensive Django web application that digitizes every aspect of library operations. It supports three distinct user roles — **Student**, **Librarian**, and **Admin** — each with a tailored dashboard and permission set.

<div align="center">

| 🎓 Students | 📚 Librarians | 🛡️ Admins |
|:---:|:---:|:---:|
| Browse & request books | Approve & issue books | Full system control |
| Read PDFs online | Manage inventory | Analytics & reports |
| Pay fines online | Track overdue books | User management |
| Get email alerts | Export records | Database backup |

</div>

---

## 🏗️ Tech Stack

<div align="center">

| Layer | Technology |
|---|---|
| **Framework** | Django 6.0.4 |
| **REST API** | Django REST Framework 3.14 |
| **Authentication** | django-allauth 65 (Email + Google + GitHub OAuth) |
| **Frontend** | Bootstrap 5 + Crispy Forms (server-rendered) |
| **Database** | PostgreSQL (local via psycopg2) |
| **Media Storage** | Local filesystem (`/media/`) |
| **Background Tasks** | Celery (eager/sync mode locally, no Redis required) |
| **Payments** | Stripe (international) + Chapa (Ethiopian ETB) |
| **Static Files** | WhiteNoise |
| **PDF Generation** | ReportLab |
| **QR Codes** | qrcode[pil] |
| **Excel Export** | openpyxl |
| **Image Processing** | Pillow |
| **Email** | Gmail SMTP (async background threads) |

</div>

---

## 🗂️ Project Structure


```
smart-library/
│
├── apps/
│   ├── users/          # Auth, profiles, roles, notifications
│   ├── books/          # Book inventory, categories, reviews
│   ├── borrow/         # Requests, borrow records, overdue
│   ├── dashboard/      # Analytics, reports, system admin
│   ├── payments/       # Stripe & Chapa fine payments
│   └── api/            # REST API (DRF ViewSets)
│
├── library_system/
│   ├── settings.py     # Main settings (local)
│   ├── urls.py         # Root URL configuration
│   ├── celery.py       # Celery + beat schedule
│   ├── email_backend.py
│   └── wsgi.py
│
├── templates/
│   ├── users/          # Auth, profile, user management
│   ├── books/          # Book list, detail, PDF reader
│   ├── borrow/         # Requests, history, overdue
│   ├── dashboard/      # Role dashboards, analytics
│   ├── payments/       # Payment flow, receipts
│   ├── emails/         # HTML + TXT email templates
│   └── includes/       # Shared nav, toasts, styles
│
├── static/             # CSS, JS, images
├── media/              # Covers, PDFs, profiles, QR codes
├── db.sqlite3          # Database (ready to use)
├── .env                # Environment variables
├── manage.py
├── requirements.txt
├── setup.bat           # First-time setup (Windows)
└── run.bat             # Start server (Windows)
```



---

## 🚀 Quick Start

### 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### 2 — Run the server

```bash
python manage.py runserver 8080
```

### 3 — Open in browser

```
http://127.0.0.1:8080
```

> **Windows users:** Just double-click `setup.bat` — it does steps 1 and 2 automatically.
> Next time use `run.bat` to start directly.

💡 Tip: After creating your superuser, log in at /admin/ and set the user's role to admin in the Users section, then visit the main site.

🎓 Student Features
<details> <summary><b>📖 Browse & Discover Books</b></summary>
Browse the full book catalog with cover images, ratings, and availability status
Search by title, author, or ISBN
Filter by category, language, and availability (available / unavailable)
View detailed book pages with description, publisher, pages, and language
See star ratings and read reviews from other students
Get personalized recommendations based on your borrowing history
View books from the same category as related suggestions
</details> <details> <summary><b>📥 Request & Borrow Books</b></summary>
Submit a book request for any available book
Join the waitlist automatically when all copies are borrowed — get notified by email when a copy becomes available
Track your requests: Pending → Approved → Fulfilled
Cancel pending or approved requests at any time
View all active borrows with due dates and days remaining
See recently rejected and cancelled requests with reasons
View borrow history (last 90 days of returned books)
Borrow limit enforced per user (default 7, configurable by admin)
</details> <details> <summary><b>📄 PDF Reader</b></summary>
Read borrowed books directly in the browser — no download required
Access-controlled: only students who have an active borrow can read
Admins and librarians can read any book
Inline PDF viewer with full browser controls
</details> <details> <summary><b>⭐ Reviews & Ratings</b></summary>
Leave a 1–5 star rating and written review for any book you've borrowed and returned
Edit your existing review at any time
See the rating distribution (star breakdown) on every book page
Average rating auto-updates when reviews are added or edited
</details> <details> <summary><b>💰 Fines & Payments</b></summary>
View outstanding fines on your dashboard and borrowed books page
Unpaid fines block new book requests — pay first to continue borrowing
Pay fines online via:
💳 Stripe — international card payments (USD)
📱 Chapa — Ethiopian mobile payments (ETB): Telebirr, CBE Birr, eBirr, M-Pesa, Bank Transfer
Download a payment receipt after successful payment
View full payment history
</details> <details> <summary><b>🔔 Notifications</b></summary>
In-app notification bell with unread count badge
Notifications for: overdue books, books due soon (within 3 days), approved requests, rejected requests
Mark individual notifications as read or delete them
Clear all notifications at once
Email alerts for all key events (see Email Notifications)
</details> <details> <summary><b>👤 Profile & Account</b></summary>
View and edit personal information (name, email, phone, address) inline — no page reload
Upload / change profile picture via AJAX
Change password securely (AJAX, session preserved)
View reading badge: Reader → Book Lover → Avid Reader (based on books read)
Download your Library ID Card as a PNG image
View borrow history with search and status filter
Password reset via email (forgot password flow)
</details>
📚 Librarian Features
<details> <summary><b>📋 Pending Requests Dashboard</b></summary>
See all pending book requests from students in real time
View book availability before approving
Check if the student has unpaid fines (blocks approval automatically)
Approve a request — automatically creates a borrow record, decrements available copies, and sends an approval email to the student
Reject a request with a reason — student is notified by email
Notification badge shows count of pending requests at all times
</details> <details> <summary><b>📤 Issue & Return</b></summary>
View all currently borrowed and overdue books in one place
Search by student name or book title
Filter by status: Borrowed / Overdue
Process returns — calculates fine automatically, updates availability, notifies waitlist
See fine amount on return and prompt for collection
</details> <details> <summary><b>📦 Book Management</b></summary>
Add new books with: ISBN (10/13 validated), title, author, category, cover image, PDF file, publisher, publication date, language, page count
QR code auto-generated for every book on save
Edit book details
Manage stock — add or remove copies, set available count, see borrowed vs available breakdown
View low-stock alerts (≤ 2 copies available)
Bulk import books from CSV or Excel (with optional ZIP of cover images and PDFs)
Download a CSV/Excel import template
</details> <details> <summary><b>🗂️ Categories</b></summary>
Create and edit book categories
View all books within a category
Category-based filtering on the book catalog
</details> <details> <summary><b>📊 Borrow Records</b></summary>
View all borrow records across all students
Search and filter by status, student, or book
Export all borrow records to CSV or Excel
View overdue books with fine totals (paid vs unpaid), including USD equivalent
</details> <details> <summary><b>📅 Calendar View</b></summary>
Visual calendar showing all due dates across all students
Color-coded: green for on-time, red for overdue
Click any event to go to the book detail page
</details> <details> <summary><b>🔔 Librarian Notifications</b></summary>
New book request alerts (with student name and book title)
Overdue book alerts (with days overdue)
Low stock alerts (books with ≤ 2 copies)
Books due today alerts
Email notifications for new requests, fine payments
</details>
🛡️ Admin Features
<details> <summary><b>📊 Admin Dashboard</b></summary>
At-a-glance stats: total books, users, active borrows, overdue count, pending requests
User role breakdown (admin / librarian / student counts)
Book availability stats (available vs unavailable, total copies)
Financial summary: total fines, unpaid fines
Recent borrows and returns feed
Most borrowed books list
30-day borrow trend chart
</details> <details> <summary><b>📈 Analytics</b></summary>
12-month borrow trend line chart
Category distribution — book count and borrow count per category
User role distribution pie chart
Book availability doughnut chart
Last 7 days daily activity — borrows vs returns per day
Top 10 most borrowed books
</details> <details> <summary><b>📋 Reports</b></summary>
This month vs last month comparison (borrows, returns, requests, fines)
All-time totals
Top 10 most borrowed books
Top 10 most active students
Overdue summary with total fines
Export reports as PDF:
📄 Overdue Books Report
📄 Fine Report (paid vs unpaid)
📄 Top 10 Books Report
📄 Top 10 Members Report
</details> <details> <summary><b>👥 User Management</b></summary>
View all users with search, role filter, and status filter
Paginated user list (20 per page)
View detailed user profile: contact info, borrow history, fines, pending requests
Change user role (admin / librarian / student)
Update borrow limit per user (1–20 books)
Deactivate user (data preserved, can reactivate)
Activate user
Delete user permanently (with username + DELETE confirmation)
Batch operations: deactivate, activate, or delete multiple users at once
Create new users (sends email verification)
Bulk import users from CSV or Excel
Download user import template
Export users to CSV or Excel
Send bulk email to selected users or all users by role
Download Library ID Card for any user
</details> <details> <summary><b>📚 Full Book Control</b></summary>
All librarian book features, plus:
Delete books (with active borrow warning)
Delete reviews (remove inappropriate content)
Download QR code for any book
Bulk import books from CSV/Excel + ZIP
</details> <details> <summary><b>💰 Overdue & Fine Management</b></summary>
View all overdue books (current and historical with paid fines)
See total fines, unpaid fines, and collected fines with ETB → USD conversion
Fine rate configurable via System Settings
Export overdue report to CSV or PDF
Export fine report to PDF
</details> <details> <summary><b>⚙️ System Administration</b></summary>
System Settings (singleton, persisted in DB):
Default borrow limit (1–20)
Fine per day (ETB)
Max borrow days (1–90)
ETB → USD exchange rate
Apply new borrow limit to all existing users at once
Activity Log — full audit trail of every action (user, action type, description, IP address, timestamp) with search and date filter
Database Backup — download a full backup (SQL via pg_dump or JSON via Django dumpdata) streamed directly to browser
Database Restore — upload a .json or .sql backup file to restore
Send due reminders manually (triggers email to all students with books due in 3 days)
Send overdue notifications manually (triggers email to all students with overdue books)
Reservation Management — view all book requests across all statuses with search and filter
</details> <details> <summary><b>📅 Calendar (Admin View)</b></summary>
See all students' due dates on one calendar
Color-coded overdue vs on-time
Click events to navigate to book detail
</details>
🔐 Authentication & Security
Feature	Detail
Registration	Email + username, email verification required before login
Email Verification	Verification link sent on register; fallback link shown on page if email fails
Resend Verification	Students can request a new verification email
Login	Username or email (case-insensitive), password
Social Login	Google OAuth and GitHub OAuth via django-allauth
Password Reset	Full forgot-password flow via email
Password Change	Inline AJAX form on profile page, session preserved
Role Guards	@admin_required, @librarian_or_admin_required, @student_required decorators
DRF Permissions	IsAdmin, IsLibrarianOrAdmin, IsStudent, IsOwnerOrLibrarianOrAdmin
Session	DB-backed sessions, 2-week cookie age
CSRF	Enforced on all forms and AJAX requests
📧 Email Notifications
All emails are sent asynchronously in background threads — no page blocking.

Trigger	Recipient	Template
Account registration	Student	Email verification link
Email verified	Student	Welcome email
Book request approved	Student	Approval + due date
Book request rejected	Student	Rejection + reason
Book due in 3 days	Student	Due soon reminder
Book overdue	Student	Overdue alert + fine amount
Book available (waitlist)	Student	Availability notification + queue position
Fine paid successfully	Student	Payment receipt
Password changed	Student	Security alert
New book request	All librarians & admins	New request notification
Fine paid	All librarians & admins	Fine collection notification
Server 500 error	All admins	Error alert with traceback
💡 In development, if SMTP is not configured, emails print to the console in readable plain-text format via the custom ReadableConsoleEmailBackend.

💳 Payment System
Fine payments support two gateways:

Stripe (International)
Card payments in USD
ETB fine amount converted using the configurable exchange rate
Minimum charge enforced ($0.50 USD)
Webhook support for async confirmation
Payment intent flow with client-side confirmation
Chapa (Ethiopian)
Payments in ETB
Supported methods: Telebirr, CBE Birr, eBirr, M-Pesa, Bank Transfer
Redirect-based checkout
Webhook + callback confirmation
Both gateways:

Create a Payment record linked to the BorrowRecord
Mark fine_paid = True on the borrow record on success
Send confirmation email to student
Notify librarians/admins
Generate a downloadable receipt
🔌 REST API
Base URL: /api/

Authentication: Session or Token (Authorization: Token <token>)

Endpoints
Resource	Method	URL	Permission
Books	GET	/api/books/	Authenticated
Books	POST	/api/books/	Librarian / Admin
Books	GET	/api/books/{id}/	Authenticated
Books	PUT/PATCH	/api/books/{id}/	Librarian / Admin
Books	DELETE	/api/books/{id}/	Librarian / Admin
Books	GET	/api/books/available/	Authenticated
Books	POST	/api/books/{id}/borrow/	Student
Categories	GET	/api/categories/	Authenticated
Categories	GET	/api/categories/{id}/	Authenticated
Borrows	GET	/api/borrows/	Role-filtered
Borrows	POST	/api/borrows/	Student
Borrows	GET	/api/borrows/{id}/	Owner / Staff
Borrows	POST	/api/borrows/{id}/return_book/	Librarian / Admin
Borrows	GET	/api/borrows/overdue/	Librarian / Admin
Borrows	GET	/api/borrows/my_borrows/	Authenticated
Users	GET	/api/users/	Librarian / Admin
Users	GET	/api/users/{id}/	Librarian / Admin
Users	GET	/api/users/me/	Authenticated
Filtering & Search:

Books: filter by category, language; search title, author, isbn; order by title, rating, times_borrowed
Borrows: filter by status, user; search book__title, user__username
Pagination: 20 items per page

---

## ⚙️ Configuration

### Key Settings (`library_system/settings.py`)

```python
AUTH_USER_MODEL = 'users.User'

MAX_BORROW_LIMIT = 5          # System default (overridden by SystemSettings)
FINE_PER_DAY = 2              # ETB per day overdue
BORROW_DURATION_DAYS = 14     # Default loan period
CURRENCY_SYMBOL = 'ETB'

CELERY_TASK_ALWAYS_EAGER = True   # No Redis needed locally

STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
CHAPA_SECRET_KEY  = config('CHAPA_SECRET_KEY',  default='')
```

### Celery Beat Schedule

| Task | Schedule |
|---|---|
| Mark overdue books | Daily at midnight |
| Send due-soon reminders | Daily at 9 AM |
| Send overdue reminders | Daily at 10 AM |
| Calculate fines | Daily at 11 PM |
| Check waitlist & notify | Every hour |

---

## 🗄️ Data Models

```
User (AbstractUser)
 ├── role: admin | librarian | student
 ├── email (unique)
 ├── phone_number, address
 └── UserProfile (OneToOne)
      ├── max_books_allowed
      ├── currently_borrowed
      ├── total_fines
      ├── profile_picture
      ├── reading_badge: reader | book_lover | avid_reader
      └── total_books_read

Category
 └── Books (ForeignKey)

Book
 ├── isbn (unique, ISBN-10/13 validated)
 ├── title, author, description
 ├── category (FK → Category)
 ├── total_copies, available_copies
 ├── cover_image, pdf_file
 ├── publisher, publication_date, pages, language
 ├── rating (auto-calculated from reviews)
 ├── times_borrowed
 ├── qr_code (auto-generated)
 └── BookReview (FK)
      ├── user (FK → User)
      ├── rating (1–5)
      └── review_text

BookRequest
 ├── user (FK → User)
 ├── book (FK → Book)
 ├── status: pending | ready | fulfilled | cancelled | rejected
 ├── approved_by (FK → User)
 └── rejection_reason, cancellation_reason

BorrowRecord
 ├── user (FK → User)
 ├── book (FK → Book)
 ├── book_request (FK → BookRequest)
 ├── borrow_date, due_date, return_date
 ├── status: borrowed | returned | overdue
 ├── fine_amount (auto-calculated)
 ├── fine_paid
 ├── issued_by, returned_to (FK → User)
 └── Payment (FK)
      ├── amount, currency
      ├── payment_method: stripe | chapa
      ├── status: pending | processing | completed | failed | refunded
      ├── transaction_id
      ├── StripePayment (OneToOne)
      └── ChapaPayment (OneToOne)

SystemSettings (singleton)
 ├── default_borrow_limit
 ├── fine_per_day
 ├── max_borrow_days
 └── etb_to_usd_rate

ActivityLog
 ├── user (FK → User)
 ├── action (21 action types)
 ├── description, ip_address, user_agent
 └── created_at
```

---

## 🔧 Management Commands

```bash
# Overdue & fines
python manage.py update_overdue_books
python manage.py calculate_fines
python manage.py send_due_soon_notifications
python manage.py send_overdue_reminders

# Utilities
python manage.py generate_qr_codes
python manage.py fix_book_ratings
python manage.py ensure_user_profiles
python manage.py cleanup_unverified_users
```

---

## 🌐 URL Reference

| URL | Access |
|---|---|
| `/` | Public |
| `/users/register/` | Public |
| `/users/login/` | Public |
| `/users/password-reset/` | Public |
| `/books/` | Public |
| `/books/<id>/` | Public |
| `/books/<id>/read/` | Authenticated + borrowed |
| `/borrow/request-list/` | Student |
| `/borrow/my-books/` | Student |
| `/borrow/history/` | Student |
| `/borrow/pending-requests/` | Librarian+ |
| `/borrow/issue-return/` | Librarian+ |
| `/borrow/overdue/` | Librarian+ |
| `/payments/select-method/<id>/` | Student |
| `/payments/history/` | Student |
| `/dashboard/` | Authenticated |
| `/dashboard/admin-dashboard/` | Admin |
| `/dashboard/librarian/` | Librarian+ |
| `/dashboard/student/` | Student |
| `/dashboard/analytics/` | Admin |
| `/dashboard/reports/` | Admin |
| `/dashboard/calendar/` | Authenticated |
| `/dashboard/system/` | Admin |
| `/users/list/` | Admin |
| `/api/` | Authenticated |
| `/admin/` | Superuser |

---

## 🐛 Troubleshooting

**Port already in use**
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

**Missing migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Email not sending locally**
```
Set EMAIL_BACKEND=library_system.email_backend.ReadableConsoleEmailBackend
in your .env to print emails to the console instead.
```

**Static files not loading**
```bash
python manage.py collectstatic
```

---

<div align="center">

Made with ❤️ using **Django 6** · **Bootstrap 5** · **SQLite**

*Smart Library Management System — Local Edition*

</div>