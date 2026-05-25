from fastapi import FastAPI
from app.core.database import Base, engine
from app.models.test_model import Test
from app.models.user_model import User
from app.models.transaction_model import Transaction
from app.models.category_model import Category
from app.routes.auth_routes import router as auth_router
from app.routes.user_routes import router as user_router
from app.routes.transaction_routes import router as transaction_router
from app.routes.category_routes import router as category_router
from app.routes.analytics_routes import router as analytics_router
from app.middleware.error_handler import add_error_handlers

# Auto-create tables for local development fallback
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Expense Tracker API",
    version="1.0.0"
)

# Register global error handlers
add_error_handlers(app)

# Include routes
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(transaction_router)
app.include_router(category_router)
app.include_router(analytics_router)

@app.on_event("startup")
def startup_populate():
    from app.core.database import SessionLocal
    from app.utils.seed_db import seed_default_categories
    db = SessionLocal()
    try:
        seed_default_categories(db)
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "API Running"}