"""
RK Residency Hub: Hotel Booking & Management Platform — FastAPI entrypoint.

Run locally with:
    uvicorn main:app --reload
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Configured once, here, before anything else runs. Without this, Python's
# root logger defaults to WARNING and every logger.info() call in the app
# (including the email console fallback in utils/email.py, used whenever
# SMTP isn't configured) is silently dropped — worth getting right since
# that fallback is the only way to see "sent" emails in local development.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from api.amenity_routes import router as amenity_router
from api.analytics_routes import router as analytics_router
from api.auth_routes import router as auth_router
from api.audit_routes import router as audit_router
from api.booking_routes import router as booking_router
from api.floor_routes import router as floor_router
from api.maintenance_routes import router as maintenance_router
from api.notification_routes import router as notification_router
from api.payment_routes import router as payment_router
from api.review_routes import router as review_router
from api.room_routes import router as room_router
from api.room_type_routes import router as room_type_router
from api.report_routes import router as report_router
from api.user_routes import router as user_router
from config.settings import settings
from middleware.error_handler import register_exception_handlers

app = FastAPI(
    title="RK Residency Hub: Hotel Booking & Management Platform",
    description="Backend API for hotel operations: bookings, rooms, maintenance, and analytics.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(floor_router)
app.include_router(room_type_router)
app.include_router(amenity_router)
app.include_router(room_router)
app.include_router(booking_router)
app.include_router(payment_router)
app.include_router(maintenance_router)
app.include_router(review_router)
app.include_router(notification_router)
app.include_router(analytics_router)
app.include_router(report_router)
app.include_router(audit_router)


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {"success": True, "message": "RK Residency Hub API is running", "data": {"status": "ok"}}
