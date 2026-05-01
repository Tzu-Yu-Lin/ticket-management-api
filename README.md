# Ticket Management API

A professional FastAPI service for managing support tickets with SQLite.

## Highlights

- Clear application package structure
- Ticket status and priority validation
- Filter, search, and pagination support
- Health check and ticket metrics endpoints
- Automatic `created_at` and `updated_at` tracking
- Backward-compatible ticket status update route
- Pytest-based API tests
- Environment-based configuration

## Project Structure

```text
ticket-management-api/
|-- app/
|   |-- config.py
|   |-- database.py
|   |-- main.py
|   |-- repository.py
|   `-- schemas.py
|-- tests/
|   `-- test_api.py
|-- .env.example
|-- main.py
|-- pyproject.toml
|-- requirements.txt
`-- requirements-dev.txt
```

## Requirements

- Python 3.11+
- SQLite

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

For development tools:

```bash
pip install -r requirements-dev.txt
```

## Run

```bash
uvicorn main:app --reload
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Configuration

Copy `.env.example` to `.env` and adjust values as needed.

Available settings:

- `APP_NAME`
- `APP_VERSION`
- `APP_DESCRIPTION`
- `DATABASE_PATH`
- `DEFAULT_PAGE_SIZE`
- `MAX_PAGE_SIZE`

## API Endpoints

### System

- `GET /` - service info
- `GET /health` - database connectivity check

### Tickets

- `POST /tickets` - create a ticket
- `GET /tickets` - list tickets with filters
- `GET /tickets/{ticket_id}` - get a ticket by ID
- `PATCH /tickets/{ticket_id}` - update ticket fields
- `PUT /tickets/{ticket_id}/status` - update only the ticket status
- `DELETE /tickets/{ticket_id}` - delete a ticket
- `GET /tickets/metrics/summary` - ticket counts by status

## Query Parameters

`GET /tickets` supports:

- `status`: `open`, `in_progress`, `resolved`, `closed`
- `priority`: `low`, `medium`, `high`, `urgent`
- `search`: searches title and description
- `limit`: page size
- `offset`: pagination offset

## Example Request

```json
{
  "title": "Checkout failure",
  "description": "Payment flow is failing for multiple customers.",
  "priority": "urgent"
}
```

## Testing

```bash
pytest
```

## Notes

- Existing databases are migrated automatically to include `priority` and `updated_at`.
- SQLite indexes are created for more efficient status and priority queries.
