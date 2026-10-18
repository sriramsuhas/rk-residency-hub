# RK Residency Hub: Hotel Booking & Management Platform

A full-stack web application for running a small hotel or residency. Guests can
browse rooms, book them, pay (mock payment), download invoices, raise
maintenance requests and leave reviews. Staff handle check-ins, maintenance
work and day-to-day operations. The owner manages rooms and users, and sees
analytics and reports, all backed by a role-based REST API.

**Stack:** FastAPI · SQLAlchemy · PostgreSQL · JWT · React (Vite)

---

## Table of contents

1. [Problem statement](#1-problem-statement)
2. [Features](#2-features)
3. [User roles and permissions](#3-user-roles-and-permissions)
4. [Architecture](#4-architecture)
5. [Technology stack](#5-technology-stack)
6. [Database design](#6-database-design)
7. [Major workflows](#7-major-workflows)
8. [API documentation](#8-api-documentation)
9. [Setup and installation](#9-setup-and-installation)
10. [Testing](#10-testing)
11. [Security](#11-security)
12. [Challenges and design decisions](#12-challenges-and-design-decisions)
13. [Known limitations](#13-known-limitations)
14. [Future improvements](#14-future-improvements)
15. [Project structure](#15-project-structure)

---

## 1. Problem statement

A small hotel typically runs on phone calls, paper registers and spreadsheets.
That causes recurring problems:

- **Double bookings**, because availability is tracked by hand.
- **Unclear responsibility** for guest issues.
- **No financial visibility**: revenue, occupancy and popular rooms are
  calculated manually, if at all.
- **No audit trail** of who changed what.

RK Residency Hub addresses these with one system:

| Problem | How the project handles it |
|---|---|
| Double bookings | Date-range overlap check on the server before any booking is created |
| Unrouted guest issues | A maintenance workflow: guest raises, reception assigns, housekeeping resolves |
| No financial visibility | Dashboards and CSV/PDF reports computed from real bookings and payments |
| No accountability | Role-based access control plus an owner-readable audit log |

---

## 2. Features

### Customer
- Register, log in, log out, change password, and reset a forgotten password
  by email.
- Browse rooms with search, filters (floor, room type, price range, capacity,
  amenities) and sorting, with pagination.
- View room details: images, floor, type, capacity, price, amenities, reviews
  and average rating.
- Check date availability, then reserve a room and pay with a mock payment
  method (Cash, UPI or Card).
- View **My Bookings**, pay a pending booking, cancel, and download the PDF
  invoice.
- Review a stay after check-out (one review per booking).
- Raise maintenance requests (category, priority, description, optional photo),
  track their status, and cancel them before work starts.
- In-app notification bell with an unread badge.

### Reception
- Dashboard cards: today's expected check-ins and check-outs, today's revenue,
  bookings awaiting payment.
- View and filter all bookings; check guests in and out.
- Refund the payment of a cancelled booking.
- View all maintenance requests and assign them to housekeeping staff.
- Download Revenue, Booking, Maintenance and Occupancy reports.

### Housekeeping
- Dashboard cards: rooms needing cleaning, pending maintenance, tasks completed
  today.
- **My Tasks**: accept an assigned task, then complete it with remarks and an
  optional completion photo.

### Owner
- Analytics dashboard: total and 30-day revenue, revenue and booking trend
  charts, occupancy, popular rooms, maintenance statistics.
- **Manage Rooms**: create, edit and deactivate rooms; upload a room photo;
  create floors, room types and amenities inline.
- **Manage Users**: search users, change their role, activate or deactivate
  accounts (this is how staff accounts are created from registered users).
- All reports (including the Customer report) and the **Audit Log** viewer.

### Platform-wide
- **Mock payments** (Cash, UPI, Card) and **automatic PDF invoice** generation
  (12% tax added to the booking subtotal).
- **Email** via SMTP: welcome, password reset, booking confirmation, booking
  cancellation, and maintenance created / assigned / completed. If SMTP is not
  configured, emails are written to the backend log instead of sent.
- **Role-based avatar**: each role shows a fixed icon and colour. There is no
  profile-picture upload.
- Consistent JSON response envelope and centralized error handling.

> **Backend-only capabilities.** A few API endpoints exist and are tested but
> have no screen in the React app yet: updating a room's availability or
> cleaning status, reassigning a booking to another room, editing or deleting
> floors / room types / amenities, deleting room images, and editing or deleting
> reviews. They can be used through Swagger (`/docs`).

---

## 3. User roles and permissions

There are four roles. Anyone who registers becomes a **CUSTOMER**; an **OWNER**
promotes accounts to staff roles. Permissions are enforced on the backend with
a `require_roles(...)` dependency on each route. The frontend only hides
navigation a role cannot use.

| Capability | Customer | Reception | Housekeeping | Owner |
|---|:-:|:-:|:-:|:-:|
| Browse rooms, availability, reviews (API is public) | ✔ | ✔ | ✔ | ✔ |
| Create bookings, pay, view own bookings and invoices | ✔ | | | |
| Cancel a booking | own | any | | any |
| View any booking / invoice | | ✔ | | ✔ |
| Check-in, check-out, reassign room | | ✔ | | ✔ |
| Refund a payment (booking must be cancelled) | | ✔ | | ✔ |
| Raise / view own maintenance requests | ✔ | | | |
| View all requests, assign to staff, request stats | | ✔ | | ✔ |
| Start and complete assigned tasks | | | ✔ (own tasks) | |
| Update room availability status | | ✔ | | ✔ |
| Update room cleaning status | | ✔ | ✔ | ✔ |
| Create / edit / deactivate rooms, floors, types, amenities, images | | | | ✔ |
| List users | | ✔ | | ✔ |
| Change user role or status | | | | ✔ |
| Write a review (own checked-out stay) | ✔ | | | |
| Delete a review | own | | | any |
| Owner analytics | | | | ✔ |
| Reception analytics | | ✔ | | ✔ |
| Housekeeping analytics | | | ✔ | ✔ |
| Revenue, booking, maintenance, occupancy reports | | ✔ | | ✔ |
| Customer report, audit log | | | | ✔ |

Ownership rules go beyond role checks: a booking, payment, invoice or
maintenance request is only visible to the person it belongs to (or the staff
roles above). Only the staff member a task is assigned to can start or complete
it.

---

## 4. Architecture

A simple layered monolith: one FastAPI process and one PostgreSQL database.

```
 React SPA (Vite)
      │  HTTPS + JSON, Bearer JWT
      ▼
 FastAPI application ── middleware: CORS, error handler, rate limiter
      │
      ▼
 api/           Routers. Parse input, check role, call one service method.
      │
      ▼
 services/      Business rules: validation, state transitions,
      │         notifications, emails, audit entries.
      ▼
 repositories/  Database queries only (SQLAlchemy). No business rules.
      │
      ▼
 PostgreSQL     + local filesystem (uploads/) for images and invoice PDFs
```

- **Why layers:** each layer has a single job. Rules such as "a booking cannot
  overlap another one" live in one place (the service layer) rather than being
  scattered across routes.
- **Schemas** (`schemas/`) are Pydantic models for request validation and
  response shaping.
- **Auth** (`auth/`) holds password hashing, JWT creation/verification and the
  FastAPI dependencies `get_current_user` and `require_roles`.
- **Static files:** the `uploads/` folder is mounted at `/uploads`.
- **Intentionally not used:** microservices, message queues, Redis, GraphQL,
  WebSockets, Celery, Docker, Redux, Tailwind. Notifications are fetched by
  polling.

**Frontend structure.** `AuthContext` stores the signed-in user.
`ProtectedRoute` redirects anonymous visitors to `/login` and wrong-role users
to `/`. An Axios client attaches the access token and, on a 401, tries one token
refresh and replays the request. The home route (`/`) renders a different page
per role: room browsing for customers, the bookings page for reception, My Tasks
for housekeeping and the analytics dashboard for the owner.

---

## 5. Technology stack

| Area | Technology |
|---|---|
| Backend language / framework | Python, FastAPI 0.115 |
| ORM / database | SQLAlchemy 2.0, PostgreSQL (psycopg2) |
| Validation | Pydantic 2, `email-validator` |
| Auth | JWT (`python-jose`, HS256), Passlib with bcrypt |
| PDF generation | ReportLab (invoices and reports) |
| Email | Python standard library `smtplib` |
| Backend tests | Pytest, FastAPI `TestClient` (in-memory SQLite) |
| Frontend | React 19, Vite, React Router 7, Axios, plain CSS |
| Charts | Recharts (owner dashboard only) |
| API docs | Swagger UI at `/docs`, ReDoc at `/redoc` |

Exact backend versions are pinned in `backend/requirements.txt`.

---

## 6. Database design

17 tables, created from the SQLAlchemy models by `python -m database.init_db`
(no migration tool is used).

### Tables

| Table | Purpose and key columns |
|---|---|
| `roles` | The four fixed roles (`CUSTOMER`, `RECEPTION`, `HOUSEKEEPING`, `OWNER`) |
| `users` | `full_name`, unique `email`, `phone`, `hashed_password`, `role_id`, `is_active` |
| `refresh_tokens` | Server-side refresh tokens: `user_id`, `token`, `expires_at`, `revoked` |
| `password_reset_tokens` | One-hour, single-use reset tokens: `user_id`, `token`, `expires_at`, `used` |
| `floors` | `name`, `floor_number` (both unique) |
| `room_types` | `name`, `base_price`, `max_occupancy` |
| `amenities` | `name` (unique), optional `icon` key |
| `rooms` | `room_number` (unique), `floor_id`, `room_type_id`, `price_per_night`, `capacity`, `availability_status`, `cleaning_status`, `maintenance_status`, `is_active` |
| `room_amenities` | Join table for the many-to-many relation between rooms and amenities |
| `room_images` | `room_id`, `image_url`, `is_primary` |
| `bookings` | `customer_id`, `room_id`, `check_in_date`, `check_out_date`, `num_guests`, `status`, `total_amount`, plus cancellation and check-in/out timestamps |
| `payments` | `booking_id`, `amount`, `method`, `status`, `transaction_reference`, `paid_at`, refund fields |
| `invoices` | `booking_id` (unique), `payment_id`, `invoice_number` (unique), `subtotal`, `tax_amount`, `total_amount`, `pdf_path` |
| `maintenance_requests` | `customer_id`, `room_id`, optional `booking_id`, `category`, `priority`, `status`, `assigned_staff_id`, issue and completion image URLs, `remarks`, lifecycle timestamps |
| `reviews` | `customer_id`, `room_id`, `booking_id` (unique), `rating` (1–5), `comment` |
| `notifications` | `user_id`, `title`, `message`, `type`, `is_read`, optional related entity reference |
| `audit_logs` | `user_id` (nullable), `action`, `entity_type`, `entity_id`, `details`, `created_at` |

### Relationships

```mermaid
erDiagram
    ROLES ||--o{ USERS : "has"
    USERS ||--o{ REFRESH_TOKENS : "owns"
    USERS ||--o{ PASSWORD_RESET_TOKENS : "requests"
    USERS ||--o{ BOOKINGS : "books"
    USERS ||--o{ MAINTENANCE_REQUESTS : "raises"
    USERS ||--o{ MAINTENANCE_REQUESTS : "is assigned"
    USERS ||--o{ REVIEWS : "writes"
    USERS ||--o{ NOTIFICATIONS : "receives"
    USERS ||--o{ AUDIT_LOGS : "performs"
    FLOORS ||--o{ ROOMS : "contains"
    ROOM_TYPES ||--o{ ROOMS : "categorizes"
    ROOMS ||--o{ ROOM_IMAGES : "has"
    ROOMS }o--o{ AMENITIES : "offers"
    ROOMS ||--o{ BOOKINGS : "is booked in"
    ROOMS ||--o{ MAINTENANCE_REQUESTS : "needs"
    ROOMS ||--o{ REVIEWS : "is reviewed in"
    BOOKINGS ||--o{ PAYMENTS : "paid by"
    BOOKINGS ||--o| INVOICES : "generates"
    BOOKINGS ||--o| REVIEWS : "reviewed once"
    BOOKINGS |o--o{ MAINTENANCE_REQUESTS : "may link to"
    PAYMENTS ||--o| INVOICES : "backs"
```

### Status values

| Field | Values |
|---|---|
| `bookings.status` | `PENDING_PAYMENT`, `CONFIRMED`, `CHECKED_IN`, `CHECKED_OUT`, `CANCELLED` |
| `payments.method` / `status` | `CASH`, `UPI`, `CARD` / `SUCCESS`, `REFUNDED` |
| `rooms.availability_status` | `AVAILABLE`, `BOOKED`, `OUT_OF_SERVICE` |
| `rooms.cleaning_status` | `CLEAN`, `DIRTY`, `IN_PROGRESS` |
| `maintenance_requests.status` | `PENDING`, `ASSIGNED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` |
| `maintenance_requests.category` | `AC`, `WATER`, `ELECTRICITY`, `WIFI`, `BATHROOM`, `FURNITURE`, `CLEANING`, `OTHER` |
| `maintenance_requests.priority` | `LOW`, `MEDIUM`, `HIGH`, `URGENT` |
| `notifications.type` | `BOOKING`, `PAYMENT`, `MAINTENANCE`, `SYSTEM` |

### Important design point: room status vs. booking calendar

`rooms.availability_status` describes the room's **physical state right now**
(it becomes `BOOKED` at check-in and `AVAILABLE` at check-out). It is **not** a
calendar. Whether a room is free on given dates is answered by querying the
`bookings` table for overlapping date ranges. Keeping these separate lets a
room be reserved for next month while still showing as available today.

### Seed data

`init_db` creates all tables, the four roles, and a default owner account
(`owner@rkresidency.com` / `Owner@12345`). On an empty database it also seeds
demo data: 3 floors, 3 room types (Standard, Deluxe, Suite), 5 amenities and 3
rooms (101, 102, 201). **Change the owner password before any real use.**

---

## 7. Major workflows

### 7.1 Booking, payment and invoice

```
Search rooms ─► check availability ─► create booking (PENDING_PAYMENT)
     ─► pay (CASH / UPI / CARD) ─► CONFIRMED + PDF invoice + notification + email
     ─► reception check-in (CHECKED_IN, room BOOKED)
     ─► reception check-out (CHECKED_OUT, room AVAILABLE and DIRTY)
     ─► guest review
```

Rules enforced on the server:

- Check-in cannot be in the past; check-out must be after check-in.
- Guest count cannot exceed the room's capacity; the room must be active and
  not `OUT_OF_SERVICE`.
- **Overlap check:** a new booking is rejected if another booking for the same
  room in `PENDING_PAYMENT`, `CONFIRMED` or `CHECKED_IN` overlaps the dates.
  Dates are treated as half-open intervals, so a stay that ends on the day
  another starts is allowed. A booking awaiting payment still holds the room.
- `total_amount` = nights × the room's `price_per_night`.
- Paying moves `PENDING_PAYMENT` to `CONFIRMED`, creates a `SUCCESS` payment
  with a reference such as `MOCK-1A2B3C4D5E6F`, and generates invoice
  `INV-<year>-<6-digit sequence>` with 12% tax added to the subtotal.
- A guest can cancel from `PENDING_PAYMENT` or `CONFIRMED`; reception or the
  owner can too. Check-in is only possible from `CONFIRMED`, check-out only from
  `CHECKED_IN`. There is no cancellation after check-in.
- Cancelling does not refund automatically. Reception or the owner refunds a
  `SUCCESS` payment of a cancelled booking, which marks it `REFUNDED` (no real
  money moves; the payment system is a mock).

### 7.2 Maintenance

```
Guest raises request (PENDING)
   ─► reception assigns a housekeeping user (ASSIGNED)
   ─► staff starts the task (IN_PROGRESS)
   ─► staff completes with remarks and optional photo (COMPLETED)
```

- Requests can be cancelled by the requester, reception or the owner while
  `PENDING` or `ASSIGNED`.
- The assignee must be a `HOUSEKEEPING` user. Assigning can optionally change
  the priority, and a request can be reassigned before work starts.
- Only the assigned staff member can start or complete a task.
- Events: the guest gets an email when a request is received, assigned and
  completed; the assigned staff member gets an in-app notification on
  assignment; the guest gets an in-app notification on completion.
- Everything is persisted, so statuses, history and the owner's statistics
  (average resolution time, most frequent category, staff workload) come from
  real records.

### 7.3 Authentication and password reset

1. **Login** returns an access token (30 minutes) and a refresh token (7 days).
   The refresh token is also stored in the database.
2. The frontend stores both in `localStorage` and sends the access token as a
   Bearer header. On a 401 it requests a new access token with the refresh token
   once and retries the call; if that fails the user is sent to the login page.
3. **Logout** revokes the submitted refresh token. Changing or resetting a
   password revokes all of the user's refresh tokens.
4. **Forgot password:** the backend creates a random one-hour, single-use token
   and emails a link to `FRONTEND_BASE_URL/reset-password?token=...`. The
   response is identical whether or not the email exists, and the token is never
   returned by the API.
5. Deactivated accounts cannot log in or use existing tokens.

### 7.4 Notifications and email

- **In-app notifications** are created for: payment success (booking
  confirmed), refunds, maintenance assignment (to staff) and maintenance
  completion (to the guest). The bell polls every 30 seconds; users can mark one
  or all as read.
- **Email** is sent for: welcome, password reset, booking confirmation (on
  payment), booking cancellation, and maintenance created / assigned /
  completed. Sending never breaks the request that triggered it: failures are
  logged and ignored.

### 7.5 Reports, analytics and audit

- **Dashboards** read live data. Owner: revenue, 30-day trends, occupancy
  snapshot (rooms currently `BOOKED` / active rooms), top 5 rooms by
  non-cancelled bookings, customer growth, maintenance stats. Reception and
  housekeeping dashboards are described in [Features](#2-features). "Today" is
  calculated in UTC.
- **Reports** (CSV or PDF, default range last 30 days): Revenue, Booking,
  Maintenance, Occupancy (historical, per day, derived from booking dates and
  capped at 92 days per request) and Customer (owner only).
- **Audit log:** registrations, logins/logouts, password events, role and status
  changes, room changes, bookings, payments, refunds and maintenance changes are
  recorded. The owner can filter by action, entity type, user and date.

---

## 8. API documentation

Interactive docs are generated by FastAPI: start the backend and open
**`http://localhost:8000/docs`** (Swagger UI) or `/redoc`. The API has 76
operations under the `/api/v1` prefix.

**Response format.** Every JSON response uses the same envelope, including
errors:

```json
{ "success": true, "message": "Success", "data": { } }
```

Validation and domain errors return `success: false` with an appropriate status
(401, 403, 404, 409, 422, 429, 500). Report and invoice downloads return files.

### Endpoint overview

| Area | Endpoints (under `/api/v1`) |
|---|---|
| Auth | `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/forgot-password`, `/auth/reset-password`, `/auth/change-password` |
| Users | `GET/PUT /users/me`; `GET /users` (owner, reception); `PATCH /users/{id}/role`, `/users/{id}/status` (owner) |
| Catalog | `/floors`, `/room-types` (list; owner create/update/delete); `/amenities` (list; owner create/delete) |
| Rooms | `GET /rooms` (filters: `search`, `floor_id`, `room_type_id`, `min_price`, `max_price`, `capacity`, `availability_status`, `amenity_ids`, `sort_by`, `page`, `page_size`), `GET /rooms/{id}`, `GET /rooms/{id}/availability?check_in=&check_out=`, `GET /rooms/{id}/reviews`; owner: `POST/PUT/DELETE /rooms`, `PATCH /rooms/{id}/amenities`, `POST/DELETE /rooms/{id}/images`; staff: `PATCH /rooms/{id}/availability`, `/rooms/{id}/cleaning-status` |
| Bookings | `POST /bookings`, `GET /bookings/me`, `GET /bookings` (staff, filterable), `GET /bookings/{id}`, `POST /bookings/{id}/cancel`, `/check-in`, `/check-out`, `/pay`, `PATCH /bookings/{id}/assign-room`, `GET /bookings/{id}/invoice` and `/invoice/pdf` |
| Payments | `GET /payments/me`, `GET /payments/{id}`, `POST /payments/{id}/refund` |
| Maintenance | `POST /maintenance-requests` (multipart), `GET /maintenance-requests/me`, `/my-tasks`, `/stats`, list, `GET /{id}`, `PATCH /{id}/assign`, `POST /{id}/start`, `/{id}/complete` (multipart), `/{id}/cancel` |
| Reviews | `POST /reviews`, `GET /reviews/me`, `PUT/DELETE /reviews/{id}` |
| Notifications | `GET /notifications`, `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all` |
| Analytics | `GET /analytics/owner`, `/analytics/reception`, `/analytics/housekeeping` |
| Reports | `GET /reports/revenue`, `/bookings`, `/maintenance`, `/occupancy`, `/customers` with `format=csv` or `format=pdf` |
| Audit | `GET /audit-logs` (owner) |
| Health | `GET /health` |

Room search, room detail, availability, reviews and the catalog lists are public
at the API level. Each operation's exact role requirement is visible in Swagger
and summarised in [section 3](#3-user-roles-and-permissions).

---

## 9. Setup and installation

### Prerequisites
- Python 3.11+ (developed and tested on 3.12)
- Node.js 18+
- PostgreSQL 14+

### 1. Create the database

```sql
CREATE USER rk_user WITH PASSWORD 'rk_password';
CREATE DATABASE rk_pms_db OWNER rk_user;
```

### 2. Configure environment

From the repository root:

```bash
cp .env.example .env
```

Edit `.env` (at minimum `DATABASE_URL` and a long random `JWT_SECRET_KEY`).
The backend reads `../.env` relative to the directory it is started from, so
**start it from `backend/`**.

| Variable | Purpose | Default / example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://rk_user:rk_password@localhost:5432/rk_pms_db` |
| `JWT_SECRET_KEY` | Token signing key. Set a long random value | `change_this_to_a_long_random_secret` |
| `JWT_ALGORITHM` | Signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:5173` |
| `MAX_UPLOAD_SIZE_MB` | Image upload size limit | `5` |
| `UPLOAD_DIR` | Folder for uploads and invoices | `uploads` |
| `SMTP_HOST` | SMTP server. **Leave blank to log emails to the console** | blank |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | SMTP credentials | blank |
| `EMAIL_FROM` | Sender shown on emails | `RK Residency Hub <no-reply@rkresidencyhub.example>` |
| `SMTP_USE_TLS` | Use STARTTLS | `true` |
| `FRONTEND_BASE_URL` | Used to build links in emails | `http://localhost:5173` |
| `APP_ENV` | Present in `.env.example` and settings but not currently used by any logic | `development` |

Never commit a real `.env` or SMTP credentials.

### 3. Run the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m database.init_db          # tables, roles, owner account, demo data
uvicorn main:app --reload           # http://localhost:8000
```

### 4. Run the frontend

```bash
cd frontend
npm install
cp .env.example .env                # VITE_API_BASE_URL=http://localhost:8000
npm run dev                         # http://localhost:5173
```

### 5. Try it

1. Log in as the owner (`owner@rkresidency.com` / `Owner@12345`).
2. Register a second account (it becomes a customer) and promote it to
   `RECEPTION` or `HOUSEKEEPING` under **Users**.
3. As a customer, book a room, pay, and open My Bookings for the invoice.

### Email in development

With `SMTP_HOST` blank, the full email (subject and body, including the real
password-reset link) is printed in the terminal running `uvicorn`. To send real
mail, set the `SMTP_*` and `EMAIL_FROM` variables for your provider (Gmail SMTP,
Mailtrap, SendGrid, etc.).

### Database changes

The schema is created with `create_all`, which does **not** alter existing
tables. If you change models, recreate the database (or add a migration tool).

---

## 10. Testing

```bash
cd backend
pytest -v
```
Tests use an in-memory SQLite
database with the four roles pre-seeded, so no PostgreSQL server or mail server
is needed. They run through FastAPI's `TestClient`, so they exercise the real
routes, services and repositories.

Covered areas: authentication and password reset, user and role management,
rooms / floors / room types / amenities, booking rules (overlap, capacity,
status transitions, access control), payments, invoices and refunds,
maintenance workflow and ownership rules, reviews and notifications,
analytics values, CSV/PDF reports, audit log, upload validation, and rate
limiting.

There are **no automated frontend tests**. The frontend is verified by
building it (`npm run build`) and by manual use.

---

## 11. Security

| Concern | Implementation |
|---|---|
| Passwords | bcrypt via Passlib; length 8–72 characters |
| Authentication | JWT (HS256) with `type`, `role` and unique `jti` claims; access tokens expire after 30 min |
| Refresh tokens | Stored in the database and revocable; revoked on logout, password change and password reset |
| Authorization | `require_roles(...)` on routes plus ownership checks in services (a user cannot read another user's booking, payment, invoice or request) |
| Password reset | Random single-use token, 1-hour expiry, delivered only by email; uniform response prevents account enumeration |
| Brute-force protection | In-memory rate limiter: 10 requests per 60 seconds per IP, shared by register, login and forgot-password (HTTP 429) |
| SQL injection | SQLAlchemy ORM / Core with bound parameters; no string-built SQL |
| Input validation | Pydantic schemas for bodies and typed/constrained query parameters |
| File uploads | Only JPEG, PNG or WEBP, up to 5 MB, non-empty. The saved extension comes from the validated Content-Type, never from the client filename, and files get random UUID names |
| Error handling | Central handlers return a uniform envelope; unexpected errors return a generic 500 and are logged |
| CORS | Allow-list from `CORS_ORIGINS` (not a wildcard) |
| Auditing | Security-relevant actions are written to `audit_logs` and readable by the owner |

---

## 12. Challenges and design decisions

These are real issues encountered while building, and how the code handles them.

- **Calendar vs. physical status.** Mixing "is the room free on these dates"
  with "is someone in the room now" breaks down quickly. The booking table is
  the calendar; `availability_status` only reflects current occupancy.
- **Pending payments must hold the room.** If unpaid bookings did not block
  dates, two guests could reserve the same nights while one was paying. The
  overlap query therefore counts `PENDING_PAYMENT` bookings.
- **Enum values in text.** SQLAlchemy returns Python enum members, so putting a
  status in an f-string printed `BookingStatus.CONFIRMED` instead of
  `CONFIRMED`. A small helper (`utils/enum_utils.py`) normalizes values for
  messages and PDFs.
- **Upload extension spoofing.** Taking the extension from the client filename
  would let a crafted upload write an unexpected file type into a publicly
  served folder. A shared upload helper (`utils/uploads.py`) derives it from the
  validated Content-Type instead.
- **Duplicate JWTs.** Two tokens issued in the same second were identical and
  collided on the refresh-token unique constraint. A random `jti` claim fixes it.
- **Validation errors not serializable.** Pydantic includes exception objects
  in error context; the error handler strips them so the response stays valid
  JSON.
- **Rate limiter in tests.** A module-level limiter shared across tests would
  cause false 429s, so the test client overrides it, and a separate test
  verifies the real limiter.
- **Invisible log output.** Python drops `INFO` logs unless logging is
  configured, which would hide the development email fallback. `main.py`
  calls `logging.basicConfig(level=logging.INFO)`.
- **Staying simple.** Avoiding extra infrastructure (queues, caches,
  containers) keeps the system easy to run and explain; the trade-offs are
  listed below.

---

## 13. Known limitations

Stated plainly so nothing is oversold:

- **Uploaded files are publicly readable.** `/uploads` is served as static
  files without authentication, and this includes generated invoice PDFs
  (`/uploads/invoices/INV-<year>-<number>.pdf`, which have predictable names).
  The authenticated invoice endpoint exists, but the static path bypasses it.
  Do not use real customer data until invoices are served only through the
  authenticated route.
- **The React app requires login for every page** except login, register and
  password reset, even though the API allows anonymous room browsing.
- **JWTs are kept in `localStorage`**, which is exposed to any XSS bug.
- **Refresh tokens are not rotated.** Refreshing returns a new access token
  only.
- **The rate limiter is in-memory and per process**; it resets on restart and
  is not shared across multiple instances.
- **Upload validation trusts the Content-Type header**; file signatures are not
  inspected.
- **Payments are mocked.** No payment gateway; "refund" only updates a status.
- **`rooms.maintenance_status` is never updated.** The field exists and is
  returned by the API, but the maintenance workflow does not change it.
  `NotificationType.SYSTEM` is also defined but unused.
- **Maintenance requests are not linked to bookings in the UI.** The API
  accepts an optional `booking_id`, but the frontend does not send it.
- **Notifications are limited** to the events listed in
  [7.4](#74-notifications-and-email): for example, reception is not notified
  when a request is created, and booking cancellation sends an email but no
  in-app notification.
- **Emails are plain text**, and there is no database migration tool (see
  [Database changes](#database-changes)).
- **Backend-only operations** listed in [Features](#2-features) have no UI.
- The default owner password and demo data are for development only.

---

## 14. Future improvements

- Serve invoices and other private files only through authenticated endpoints.
- Allow public room browsing and the booking widget before login.
- Frontend screens for room cleaning/availability updates, room reassignment,
  editing floors/types/amenities, and editing reviews.
- Notify reception when a maintenance request is created, and update
  `rooms.maintenance_status` from the maintenance workflow.
- Rotate refresh tokens, move tokens to HTTP-only cookies, and verify upload
  file signatures.
- Add database migrations (e.g. Alembic) and frontend automated tests.
- HTML email templates and a real payment gateway integration.
- Pagination controls on the Manage Users and Audit Log tables.

---

## 15. Project structure

```
.
├── backend/
│   ├── main.py             App setup: logging, CORS, error handlers, routers, /uploads
│   ├── api/                14 routers (auth, users, floors, room-types, amenities, rooms,
│   │                       bookings, payments, maintenance, reviews, notifications,
│   │                       analytics, reports, audit)
│   ├── services/           Business logic
│   ├── repositories/       Database access
│   ├── models/             SQLAlchemy models and enums (17 tables)
│   ├── schemas/            Pydantic request/response models
│   ├── auth/               Password hashing, JWT, auth/role dependencies
│   ├── middleware/         Exception handlers, rate limiter
│   ├── config/             Settings loaded from environment
│   ├── database/           Engine/session and init_db seed script
│   ├── utils/              Email + templates, uploads, report builder, helpers
│   ├── uploads/            Room images, maintenance photos, invoices
│   ├── tests/              Pytest suite (135 tests)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/            Axios client and endpoint wrappers
│       ├── context/        AuthContext
│       ├── components/     TopNav, ProtectedRoute, NotificationBell, RoleAvatar, layouts
│       ├── pages/          Role-specific pages (listing, details, bookings, tasks,
│       │                   dashboards, manage rooms/users, reports, audit log, ...)
│       └── styles/         Shared form and status styles
├── docs/                   Design notes written during development, plus
│   └── diagrams/           Mermaid diagrams (architecture, flows, ER)
├── .env.example
└── README.md
```
