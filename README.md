# RK Residency Hub: Hotel Booking & Management Platform

A full-stack hotel booking and property management platform: guest room
browsing and booking, staff operations, maintenance workflows, real email
notifications, and owner analytics — built on a clean layered backend and a
simple, role-aware React frontend.

> **Status:** Feature-complete and actively maintained. See [docs/](docs)
> for the module-by-module build log, [docs/diagrams/](docs/diagrams) for
> the system design diagrams (ER diagram, architecture, request flow,
> booking and maintenance workflows, auth flow), and
> [docs/module9_security_review.md](docs/module9_security_review.md) for
> the full security checklist.

## Project overview

RK Residency Hub models a small residency/hotel with four roles —
**Customer**, **Reception**, **Housekeeping**, and **Owner** — each with a
distinct set of permissions enforced server-side via JWT + role-based
access control. Room booking is the platform's central experience: it's
directly accessible from the main header for every visitor, no digging
through menus required.

The backend follows a simple layered architecture:

```
React Frontend
      ↓
FastAPI REST API
      ↓
Services (business logic)
      ↓
Repositories (data access)
      ↓
PostgreSQL
```

This is deliberately not a microservices system. One process, one database,
no Redis/Kafka/Docker/Kubernetes/GraphQL/WebSockets — the whole thing is
sized to be explainable start-to-finish in an internship interview.

## Roles & what each one can do

| Role | Main functionality |
|---|---|
| **Customer** | Browse & book rooms, My Bookings, raise/track maintenance requests, notifications, profile |
| **Reception** | Dashboard, manage bookings, check-in/check-out, assign maintenance staff, view reports |
| **Housekeeping** | Dashboard, my assigned tasks, accept/complete maintenance work, room cleaning status |
| **Owner** | Dashboard/analytics, manage rooms/floors/room types/amenities, manage users & staff, reports, audit log |

Backend authorization (`require_roles()` on every mutating route) is the
real security boundary — the frontend nav only hides options a role
shouldn't see; it never relies on hiding as the actual protection.

## Features

**Authentication & accounts**
- Registration, login, logout, JWT access + rotating refresh tokens (stored
  server-side, individually revocable)
- Real email-based password reset (see [Email](#email-configuration) below)
  — no token is ever returned in an API response
- Change password, role-based access control, account activation/deactivation
- Fixed, role-specific avatar (Customer/Reception/Housekeeping/Owner) shown
  everywhere a user appears — not an uploaded image; there is no profile
  picture feature

**Rooms & hotel operations**
- Full CRUD for floors, room types, amenities, and rooms — including a
  dedicated Owner-facing **Manage Rooms** page (create, edit, deactivate,
  upload photos, quick-add floors/types/amenities inline)
- Public room search with pagination, text search, floor/type/price/capacity
  filters, amenity filtering, and sorting — no login required to browse
- Room status split cleanly into two concerns that are easy to confuse:
  `availability_status` (a live snapshot of physical occupancy, changed at
  check-in/check-out) vs. the `bookings` table (the actual date-based
  calendar, checked by date range). They are not the same thing.

**Booking**
- The full guest journey: Home → Book a Room → search available rooms →
  view details (room type, floor, capacity, price, amenities, images) →
  pick dates & guests → confirm → mock payment → confirmation → visible in
  My Bookings
- Date-range availability checking with correct interval-overlap logic
- Booking validation: no past check-ins, checkout after check-in, guest
  count within capacity, no double-booking
- Self-service cancellation while a booking is still pending payment or
  confirmed; Reception/Owner can check guests in and out

**Payments & invoices**
- Mock payment methods: Cash, UPI, Card — no real payment gateway
- A real payment gate: a booking only becomes `CONFIRMED` after a
  successful mock payment; it starts as `PENDING_PAYMENT`
- Automatic PDF invoice generation on successful payment, downloadable by
  the guest or staff with permission
- Staff-only refund flow, gated on the booking actually being cancelled

**Maintenance**
- Full three-role workflow: Customer raises a request (category, priority,
  description, optional photo) → Reception assigns it to Housekeeping →
  staff accepts, works, and completes it with remarks and an optional
  completion photo
- Status lifecycle enforced server-side: `PENDING → ASSIGNED → IN_PROGRESS
  → COMPLETED`, cancellable only before work starts
- Real in-app notifications *and* real emails at every step: request
  received, assigned, and completed
- Ownership checks throughout — only the assigned staff member can work
  their own task; a request is visible only to its raiser, its assignee,
  or Reception/Owner

**Reviews & notifications**
- Reviews tied to verified stays only (`CHECKED_OUT` bookings), one review
  per booking, editable by the author, deletable by the author or Owner
- In-app notification bell with unread badge, polling every 30 seconds —
  wired into real backend events (booking confirmed, refund processed,
  maintenance assigned/completed), not a standalone demo

**Analytics, reports & audit**
- **Owner dashboard**: revenue (total & 30-day trend chart), occupancy
  rate, booking volume chart, popular rooms, customer growth, maintenance
  stats
- **Reception dashboard**: today's expected check-ins/outs, today's
  revenue, bookings awaiting payment
- **Housekeeping dashboard**: rooms needing cleaning, pending maintenance,
  tasks completed today
- Five downloadable reports (Revenue, Booking, Maintenance, Occupancy,
  Customer) in CSV or PDF
- Owner-facing audit log — every security-relevant action (logins, role
  changes, bookings, payments, refunds, maintenance changes) is recorded
  and readable, not just written

**Security**
- Centralized, consistent JSON error responses on every endpoint
- In-memory rate limiting on register/login/forgot-password
- Secure file-upload validation: extension is derived from the *validated*
  Content-Type, never from the client-supplied filename (see the security
  review doc for the real bug this closed)
- SQL injection protection via SQLAlchemy ORM throughout — no raw/
  string-formatted SQL anywhere in the codebase

## What was intentionally removed

- **Wishlist** — removed completely: no `wishlist_items` table, no API, no
  service/repository, no frontend page or heart-toggle buttons.
- **Profile picture upload** — removed completely: no upload endpoint, no
  `profile_picture_url` field, no upload UI. Every user shows a fixed,
  role-based avatar instead.
- **Mocked password reset** — replaced with a real (or console-logged, in
  local dev) email flow; the reset token is never returned in an API
  response.

## Tech stack

**Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, Pydantic, JWT, Passlib (bcrypt), Pytest
**Frontend:** React, Vite, React Router, Axios, Recharts (dashboard charts only), plain CSS
**Docs:** Swagger/OpenAPI, Markdown, Mermaid diagrams

No Redis, Kafka, RabbitMQ, Kubernetes, GraphQL, WebSockets, Celery, Docker,
Docker Compose, Tailwind, or Redux — by design, not by omission.

## Folder structure

```
rk-pms/
├── backend/
│   ├── api/            # FastAPI routers — thin, delegate to services
│   ├── auth/            # Password hashing, JWT encode/decode, auth dependencies
│   ├── config/           # Environment-driven settings
│   ├── database/          # Engine, session, init/seed script
│   ├── middleware/         # Exception handling, rate limiting
│   ├── models/            # SQLAlchemy ORM models (17 tables)
│   ├── repositories/       # Raw DB queries only, no business logic
│   ├── schemas/           # Pydantic request/response models
│   ├── services/          # Business logic
│   ├── utils/             # Shared exceptions, uploads, email, response helpers
│   ├── uploads/           # Room images, maintenance photos, generated invoices
│   ├── tests/             # Pytest suite
│   ├── main.py            # FastAPI app entrypoint
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/           # Axios client + endpoint wrappers
│       ├── context/        # AuthContext (global auth state)
│       ├── components/      # Shared UI (nav, route guard, role avatar, notification bell)
│       ├── pages/          # Login, Register, Home, Manage Rooms, Manage Users, ...
│       └── styles/         # Shared form/button/alert/status styles
├── docs/                 # Per-module schema & API design docs
│   └── diagrams/          # ER diagram, architecture, workflow diagrams (Mermaid)
├── .env.example
└── README.md
```

## Database overview

17 tables: `roles`, `users`, `refresh_tokens`, `password_reset_tokens`,
`audit_logs`, `floors`, `room_types`, `amenities`, `rooms`, `room_images`,
`room_amenities` (join table), `bookings`, `payments`, `invoices`,
`maintenance_requests`, `reviews`, `notifications`. Full column-level detail
and relationships are in [`docs/diagrams/er-diagram.md`](docs/diagrams/er-diagram.md),
generated directly from the live SQLAlchemy models rather than drawn by hand.

Key relationships:

```
User → Bookings → Room
Room → Floor, Room → Room Type, Room ↔ Amenities
Booking → Payment → Invoice
Booking → Review (once, only after CHECKED_OUT)
Maintenance Request → User (customer), → Room, → Booking (optional), → Assigned Staff
Notifications → User
Audit Log → User
```

## Authentication

JWT access tokens (30 min) + rotating refresh tokens (7 days, stored
server-side and individually revocable — logout, password change, and
password reset all revoke them). See
[`docs/diagrams/auth-flow.md`](docs/diagrams/auth-flow.md) for the full
sequence diagram.

## Booking flow

Home → Book a Room → search available rooms → view room details (type,
floor, capacity, price, amenities, images) → select dates & guests → confirm
→ mock payment → confirmation → visible in My Bookings. Full state machine
in [`docs/diagrams/booking-workflow.md`](docs/diagrams/booking-workflow.md).

## Maintenance flow

Customer raises → Reception assigns to Housekeeping → staff accepts, works,
completes. Real-time in-app notifications and emails at each step. Full
diagram in [`docs/diagrams/maintenance-workflow.md`](docs/diagrams/maintenance-workflow.md).

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ running locally

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example ../.env         # then edit ../.env with your DB credentials
python -m database.init_db         # creates tables, seeds roles + a default Owner
uvicorn main:app --reload          # http://localhost:8000
```

The default Owner login after seeding is `owner@rkresidency.com` /
`Owner@12345` — **change this password immediately** after first login in
any non-local environment.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env               # points the app at your backend URL
npm run dev                        # http://localhost:5173
```

### Running tests

```bash
cd backend
pytest -v
```

All 135 backend tests pass as of the current codebase (run this yourself
after cloning — don't take a README's word for it).

## Environment variables

See [`.env.example`](.env.example) for the full list.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Signing key for access/refresh tokens — set a long random value in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (default 30) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime (default 7) |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins |
| `MAX_UPLOAD_SIZE_MB` | Cap on uploaded file size |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` | SMTP server for real email delivery |
| `EMAIL_FROM` | The "From" address on outgoing emails |
| `SMTP_USE_TLS` | Whether to use STARTTLS (default true) |
| `FRONTEND_BASE_URL` | Used to build links inside emails (e.g. the password reset link) |

Never commit a real `.env` file — only `.env.example` (with placeholder
values) belongs in version control.

## Email configuration

Password reset, welcome emails, booking confirmation/cancellation, and
maintenance status updates are all sent via a simple SMTP-based email
utility (`backend/utils/email.py`) — no third-party email service SDK, no
background job queue, just `smtplib` and STARTTLS.

**Local development:** leave `SMTP_HOST` blank in your `.env`. Emails are
then logged to the backend console instead of actually being sent — you'll
see the full subject and body (including the real password-reset link)
printed in the terminal running `uvicorn`. This is also what the test suite
relies on, so tests never need a real mail server.

**Real delivery:** set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`,
`SMTP_PASSWORD`, and `EMAIL_FROM` to a real SMTP provider (Gmail SMTP,
SendGrid, Mailtrap, etc.) and delivery starts working with no code changes.

The reset token is **never** included in any API response — the only way
to get it is via the emailed (or console-logged) link.

## API documentation

Interactive Swagger UI is available at `/docs` (and ReDoc at `/redoc`) once
the backend is running. Endpoint-level design notes for each module also
live in `docs/`, e.g. [`docs/module1_api.md`](docs/module1_api.md).

## System design

All required diagrams live in [`docs/diagrams/`](docs/diagrams) as
GitHub-native Mermaid — ER diagram, high-level architecture, request flow,
booking workflow, maintenance workflow, and authentication flow. Each was
generated or verified against the actual code (the ER diagram from live
schema introspection, the workflow diagrams from the real service-layer
state machines) rather than drawn from memory, and syntax-validated with
Mermaid's own parser before being committed.

## Screenshots

_Add screenshots of the Login, Register, Book a Room, and Owner Dashboard
pages here once you've run the app locally._

## Interview talking points

A few things worth being able to speak to, since they came from real
decisions and real bugs made across the build rather than being designed
perfectly upfront:

- **The booking status machine changed mid-project.** Bookings originally
  shipped as auto-`CONFIRMED` before a payment gate existed. A
  `PENDING_PAYMENT` state was retrofitted ahead of `CONFIRMED` — which meant
  updating the overlap-detection query (a pending booking still has to hold
  the room) and every existing test that assumed immediate confirmation.
- **`Room.availability_status` vs. the `bookings` table.** A room's status
  field is a live snapshot of physical occupancy (set at check-in/out), not
  a calendar. The calendar is the bookings table, queried by date range.
  Conflating those two is a common beginner mistake in booking systems.
- **A real security bug, found and fixed, not simulated.** File uploads
  used to derive their saved extension from the client-supplied filename
  rather than the validated Content-Type — a spoofed upload could have
  written an arbitrary extension into a publicly-served directory. Full
  writeup in [`docs/module9_security_review.md`](docs/module9_security_review.md).
- **A logging bug that silently swallowed the email dev-fallback.**
  `logger.info()` calls are dropped by default in Python unless the root
  logger's level is configured — meaning the "email logged to console in
  dev" feature was invisible until `logging.basicConfig(level=logging.INFO)`
  was added at app startup. Caught by actually checking the log output, not
  by trusting that a `logger.info()` call meant the message would appear.
- **A subtle Python/Enum bug that only showed up in output, not tests.**
  SQLAlchemy's `Enum` column type returns the actual Python enum member on
  read, not a plain string, despite the ORM model declaring `Mapped[str]`.
  F-string interpolation of that value printed `"BookingStatus.CONFIRMED"`
  instead of `"CONFIRMED"` — caught by actually rendering a generated PDF
  invoice and reading it.
- **Why no Redis, no microservices, no Docker.** It's the right call at
  this scale: one process, one database, layered by responsibility (routes
  → services → repositories). The rate limiter is intentionally
  single-instance-only rather than reaching for infrastructure the project
  doesn't need.

## Future improvements

- File-upload magic-byte verification beyond Content-Type checking (see
  [docs/module9_security_review.md](docs/module9_security_review.md) for
  the full list of known, documented limitations)
- Email templates as HTML (currently plain text, by design, to keep the
  implementation simple and understandable)
- Pagination controls on the Manage Users / Audit Log tables for very large
  datasets (currently a single page up to 100 rows, which comfortably
  covers a small residency's real data volume)
