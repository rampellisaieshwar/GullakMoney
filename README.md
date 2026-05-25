# Expense Tracker API

A production-ready RESTful Backend API for a personal expense tracker, built with Python, FastAPI, and PostgreSQL. It features full JWT-based authentication, user-specific data isolation, custom categories management, transaction CRUD with advanced queries, and financial analytics.

## Features

- **JWT Authentication & Security**: Complete registration, login, and profile management with token verification. Passwords are safely hashed using `bcrypt` (via `passlib`).
- **Data Isolation**: Authorization enforced at the database level. Users can only fetch, modify, or delete their own data.
- **Transactions Core**: Create, read, update, and delete transactions.
- **Advanced Queries**: Full support for pagination, sorting (by date and amount), and filtering (by type, category, and date range).
- **Categories Management**: Seeds default categories (`Food`, `Transport`, `Bills`, etc.) and allows users to define custom categories. Custom category deletion is protected if transactions are active.
- **Aggregated Analytics**: 
  - **Financial Summary**: Total income, expenses, and net balance.
  - **Spending Breakdown**: Percentages and totals grouped by category.
  - **Monthly Trends**: Month-over-month income and expenses (configurable range).
- **Global Error Handling**: Custom middleware to sanitize exceptions and standardize error formats.
- **Database Migrations**: Managed via Alembic migrations.

---

## Tech Stack & Reasoning

- **Core Framework**: **FastAPI** (Python). Chosen for high performance (comparable to Go/Node.js), native asynchronous support, Pydantic type safety, and automatic OpenAPI/Swagger docs generation.
- **Database & ORM**: **PostgreSQL** & **SQLAlchemy**. PostgreSQL provides enterprise-grade reliability, relational constraints, and rich date/analytical aggregation functions. SQLAlchemy is used as the Object-Relational Mapper (ORM) for declarative database models.
- **Migrations**: **Alembic**. Allows schema versioning and deterministic schema updates without data loss.
- **Testing**: **Pytest** & **HTTPX**. Chosen for quick, isolated execution of integration tests with automatic transaction rollback.

---

## Architecture

The project follows a modular, route-based architecture designed for clarity and maintainability:

```text
GullakMoney/
├── alembic/                # Database migrations config and scripts
├── app/
│   ├── core/               # Database and security configurations
│   ├── middleware/         # Custom exception handling middleware
│   ├── models/             # SQLAlchemy database models
│   ├── routes/             # Route controllers grouped by domain (auth, user, transactions, etc.)
│   ├── schemas/            # Pydantic validation schemas
│   └── utils/              # Dependencies, helpers, and seed scripts
├── tests/                  # Pytest test suite
├── alembic.ini             # Alembic configuration
├── pytest.ini              # Pytest configuration
├── requirements.txt        # Production & development dependencies
└── README.md
```

---

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```ini
DATABASE_URL=postgresql:///expense_tracker
SECRET_KEY=supersecretkey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## Setup Instructions

### 1. Prerequisites
Ensure you have Python 3.10+ and a PostgreSQL server running locally.

### 2. Clone and Enter Project Folder
```bash
git clone <repository-url>
cd GullakMoney
```

### 3. Initialize Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Setup PostgreSQL Database
Ensure a local PostgreSQL database exists. For example, if using the default `.env`:
```bash
createdb expense_tracker
```

### 6. Run Database Migrations
Apply migrations to construct the database schema:
```bash
alembic upgrade head
```

### 7. Run the Application
Start the Uvicorn development server:
```bash
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

---

## API Documentation

FastAPI automatically generates interactive documentation. Once the server is running, visit:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Endpoints

### Authentication (`/auth`)
- `POST /auth/register`: Register a new user.
- `POST /auth/login`: Authenticate and receive a JWT.
- `POST /auth/logout`: Stateless client logout message.

### Users (`/users`)
- `GET /users/me`: Fetch current user's profile.
- `PUT /users/me`: Update profile details (name, email).
- `POST /users/me/change-password`: Change password (requires current password validation).

### Transactions (`/transactions`)
- `POST /transactions/`: Create a transaction (validates category, accepts custom date).
- `GET /transactions/`: Fetch all transactions with support for:
  - **Pagination**: `page`, `limit` (e.g. `/transactions/?page=1&limit=10`)
  - **Filtering**: `type` (income/expense), `category` name, `start_date`, and `end_date` date range.
  - **Sorting**: `sort_by` (date, amount), `order` (asc, desc)
- `GET /transactions/{id}`: Retrieve a single transaction by ID.
- `PATCH /transactions/{id}`: Partially update a transaction.
- `DELETE /transactions/{id}`: Delete a transaction (returns `240 No Content`).

### Categories (`/categories`)
- `GET /categories/`: List all default and custom categories available to the user.
- `POST /categories/`: Create a custom category.
- `PATCH /categories/{id}`: Rename a custom category (automatically cascades changes to all transactions using it).
- `DELETE /categories/{id}`: Delete a custom category (blocked if any transactions are using it).

### Analytics (`/analytics`)
- `GET /analytics/summary`: Income, expenses, and net balance over a given period.
- `GET /analytics/categories`: Expense spending breakdown by category with amounts and percentages.
- `GET /analytics/monthly`: Month-over-month trend breakdown of income and expenses.

---

## Authentication Flow

1. **Obtain Token**: Send user credentials to `POST /auth/login`.
2. **Include in Headers**: For all protected routes, attach the token in the `Authorization` header:
   ```text
   Authorization: Bearer <your-jwt-token>
   ```
3. **Automatic Validation**: The server validates the signature, extracts the user ID, loads the user profile from the database, and injects the user context into the request handler.

---

## Testing

The test suite runs with a PostgreSQL transaction wrapper that rolls back database modifications after each test, ensuring a clean state.

To run the automated tests:
```bash
python -m pytest
```

---

## Assumptions and Trade-offs

1. **Transaction Categories as Strings**: The pre-existing schema defined the `category` column as a String. To avoid invasive migrations, we kept it as a String but created a standalone `categories` table. Category operations dynamically validate that the input matches either a system category or a custom category created by the user.
2. **Category Renaming Cascade**: If a user updates the name of a custom category, we automatically perform a database update on all their transactions to update the old category name to the new category name, ensuring data consistency.
3. **Category Deletion safety**: We prevent deletion of a category if it is in use by transactions to avoid leaving transaction records in an invalid/orphan category state.
4. **Stateless Logout**: Since JWTs are stateless, actual invalidation is handled client-side by dropping the token. We added an `/auth/logout` endpoint for API parity and easy future expansion (e.g. Redis blacklisting).

---

## Future Improvements

If given more time, the following features would enhance the application:
1. **Dockerization**: Add a `Dockerfile` and `docker-compose.yml` to orchestrate FastAPI, PostgreSQL, and pgAdmin in containerized environments.
2. **Rate Limiting**: Implement rate-limiting on sensitive auth endpoints (e.g., using `slowapi`) to prevent brute-force attacks.
3. **Refresh Tokens**: Implement a dual-token (Access + Refresh) structure with HttpOnly cookies to improve session security.
4. **Redis Caching**: Cache category lists and monthly analytics results to decrease database read loads.
