# Ticket Management API

A simple RESTful API for managing support tickets using FastAPI and SQLite.

---

## Features

* Create, view, update, and delete tickets (CRUD)
* Update ticket status
* Automatic timestamp (`created_at`)
* Built-in API docs (Swagger UI)

---

## Tech Stack

* Python, FastAPI
* SQLite
* Pydantic

---

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open: http://127.0.0.1:8000/docs

---

## API

* `POST /tickets` – create ticket
* `GET /tickets` – list tickets
* `GET /tickets/{id}` – get ticket
* `PUT /tickets/{id}/status` – update status
* `DELETE /tickets/{id}` – delete ticket

---

## Example

```json
{
  "title": "Login issue",
  "description": "User cannot log in"
}
```

---
