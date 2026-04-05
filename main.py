from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import sqlite3
from typing import List

app = FastAPI(title="Ticket Management API")

DB_NAME = "tickets.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)


class TicketStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1)


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    created_at: str


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"message": "Ticket Management API is running"}


@app.post("/tickets", response_model=TicketResponse)
def create_ticket(ticket: TicketCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tickets (title, description, status) VALUES (?, ?, ?)",
        (ticket.title, ticket.description, "open")
    )
    conn.commit()
    ticket_id = cursor.lastrowid

    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row)


@app.get("/tickets", response_model=List[TicketResponse])
def get_tickets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return dict(row)


@app.put("/tickets/{ticket_id}/status", response_model=TicketResponse)
def update_ticket_status(ticket_id: int, ticket_update: TicketStatusUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Ticket not found")

    cursor.execute(
        "UPDATE tickets SET status = ? WHERE id = ?",
        (ticket_update.status, ticket_id)
    )
    conn.commit()

    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return dict(updated_row)


@app.delete("/tickets/{ticket_id}")
def delete_ticket(ticket_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Ticket not found")

    cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()

    return {"message": f"Ticket {ticket_id} deleted successfully"}