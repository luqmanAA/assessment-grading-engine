# Assessment Grading Engine

Assessment Engine is a basic Django-based platform designed for creating, managing, and automatically grading student assessments. It supports Multiple Choice Questions (MCQ) and Short Answer questions, with an automated grading system powered by either a Mock engine or LLMs (OpenAI and Google Gemini).

## Features

- **Exam Management**: Create and manage exams with flexible metadata.
- **Question Types**: Supports both MCQ (Multiple Choice) and Short Answer questions.
- **Automated Grading**:
  - **Mock Grader**: For local development and testing without API costs.
  - **LLM Grader**: Uses OpenAI (GPT) or Google Gemini to grade short answers based on expected results.
- **Asynchronous Processing**: Background grading using Celery and Redis to fast response time.
- **API Documentation**: Interactive Swagger and Redoc documentation.
- **Sample Data**: Easy-to-use management commands to seed the database with students and sample exams.

## Tech Stack

- **Backend**: Django 6.0, Django REST Framework (DRF)
- **Database**: PostgreSQL (or SQLite for local dev)
- **Task Queue**: Celery, Redis
- **LLM Integration**: OpenAI SDK, Google GenAI SDK
- **Dependency Management**: `uv`
- **Documentation**: `drf-spectacular` (OpenAPI 3.0)

## Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) installed
- Redis server (running locally or via Docker)

## Setup and Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd assessment-engine
```

### 2. Environment Configuration
Copy the `.env.sample` file to `.env` and fill in the required values.

```bash
cp .env.sample .env
```

Key environment variables:
- `DEBUG`: Set to `True` for development.
- `GRADING_ENGINE`: `LLM` or `MOCK`.
- `LLM_PROVIDER`: `OPENAI` or `GEMINI`.
- `CELERY_BROKER_URL`: URL for your Redis instance (e.g., `redis://localhost:6379/0`).

### 3. Install Dependencies
Using `uv`:
```bash
uv sync
```

### 4. Run Migrations
```bash
uv run manage.py migrate && uv run manage.py migrate
```

### 5. Create Superuser
```bash
uv run manage.py createsuperuser
```

### 6. Seed Sample Data
The project includes commands to quickly set up a test environment.

**Seed Students:**
Creates 10 default student accounts (e.g., `student_1`, `student_2`) with the password `password123`.
```bash
uv run manage.py seed_students
```

**Generate Sample Exam:**
Creates a sample "Introduction to Computer Science" exam with MCQs and Short Answer questions.
```bash
uv run manage.py generate_sample_data
```

---

## Running the Application

### Start the Development Server
```bash
uv run manage.py runserver
```

### Start Celery Worker
In a separate terminal, ensure Redis is running and start the Celery worker to process grading tasks.
```bash
uv run celery -A main worker --loglevel=info
```

---

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- **Swagger UI**: [http://127.0.0.1:8000/api/schema/swagger-ui/](http://127.0.0.1:8000/api/schema/swagger-ui/)
- **Redoc**: [http://127.0.0.1:8000/api/schema/redoc/](http://127.0.0.1:8000/api/schema/redoc/)
- **Other Doc**: [Postman Documentation](https://documenter.getpostman.com/view/28806175/2sBXVcnYoq)

### Authentication
The API uses Token Authentication. To get a token for a student:
```bash
POST /api/token-auth/
{
    "username": "student_1",
    "password": "password123"
}
```
Include the token in the `Authorization` header for subsequent requests: `Authorization: Token <your_token>`

---

## Grading Engine Logic

The application uses a strategy pattern for grading:
- **MCQ**: Automatically graded by comparing the `selected_option` with the `is_correct` flag.
- **Short Answer**: 
  - If `GRADING_ENGINE=MOCK`: Scores are randomly assigned (0.5 to 1.0).
  - If `GRADING_ENGINE=LLM`: The answer is sent to the configured `LLM_PROVIDER` (OpenAI or Gemini) along with the `grading_prompt` defined in the Exam model.

Grading happens asynchronously after a submission is created. The `is_completed` field in the `Submission` model will be set to `True` once grading is finished.

## Development

- **Run Tests**: `uv run manage.py test`
- **Linting**: (If applicable, e.g., ruff) `uv run ruff check .`