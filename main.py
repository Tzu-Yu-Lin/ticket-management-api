import sqlite3
from contextlib import closing
from fastapi import FastAPI, HTTPException, Query

APP_NAME = "Ticket Management API"
APP_VERSION = "1.1.0"
APP_DESCRIPTION = "Simple FastAPI ticket API."
DATABASE_PATH = "tickets.db"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

VALID_STATUS = ["open", "in_progress", "resolved", "closed"]
VALID_PRIORITY = ["low", "medium", "high", "urgent"]


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                priority TEXT NOT NULL DEFAULT 'medium',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tickets_status_created_at ON tickets(status, created_at DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tickets_priority_created_at ON tickets(priority, created_at DESC)"
        )
        conn.commit()


def list_tickets(status=None, priority=None, search=None, limit=20, offset=0):
    query = ["SELECT * FROM tickets"]
    filters = []
    params = []

    if status:
        filters.append("status = ?")
        params.append(status)

    if priority:
        filters.append("priority = ?")
        params.append(priority)

    if search:
        filters.append("(title LIKE ? OR description LIKE ?)")
        like_pattern = f"%{search.strip()}%"
        params.extend([like_pattern, like_pattern])

    if filters:
        query.append("WHERE " + " AND ".join(filters))

    query.append("ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?")
    params.extend([limit, offset])

    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(" ".join(query), params)
        return [dict(row) for row in cursor.fetchall()]


def get_ticket_by_id(ticket_id):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)


def create_ticket(title, description, priority):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tickets (title, description, status, priority)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, "open", priority),
        )
        conn.commit()
        cursor.execute("SELECT * FROM tickets WHERE id = ?", (cursor.lastrowid,))
        return dict(cursor.fetchone())


def update_ticket(ticket_id, title=None, description=None, status=None, priority=None):
    current_ticket = get_ticket_by_id(ticket_id)
    if current_ticket is None:
        return None

    if title is None:
        title = current_ticket["title"]
    if description is None:
        description = current_ticket["description"]
    if status is None:
        status = current_ticket["status"]
    if priority is None:
        priority = current_ticket["priority"]

    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tickets
            SET title = ?, description = ?, status = ?, priority = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, description, status, priority, ticket_id),
        )
        conn.commit()
        cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        return dict(cursor.fetchone())


def update_ticket_status(ticket_id, status):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tickets SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, ticket_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None
        cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        return dict(cursor.fetchone())


def delete_ticket(ticket_id):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_ticket_metrics():
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) AS in_progress,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved,
                SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) AS closed
            FROM tickets
            """
        )
        row = dict(cursor.fetchone())
        for key in row:
            if row[key] is None:
                row[key] = 0
        return row


init_db()

app = FastAPI(title=APP_NAME, version=APP_VERSION, description=APP_DESCRIPTION)


@app.get("/")
def root():
    return {
        "message": "Ticket Management API is running",
        "version": APP_VERSION,
        "docs_url": "/docs",
    }


@app.get("/health")
def health_check():
    try:
        with closing(get_connection()) as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except sqlite3.Error:
        return {"status": "degraded", "database": "unavailable"}


@app.get("/tickets")
def get_tickets(
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
):
    if status is not None and status not in VALID_STATUS:
        raise HTTPException(status_code=400, detail="Invalid status")
    if priority is not None and priority not in VALID_PRIORITY:
        raise HTTPException(status_code=400, detail="Invalid priority")

    return list_tickets(
        status=status,
        priority=priority,
        search=search,
        limit=limit,
        offset=offset,
    )


@app.post("/tickets", status_code=201)
def create_new_ticket(ticket: dict):
    title = ticket.get("title")
    description = ticket.get("description")
    priority = ticket.get("priority", "medium")

    if not isinstance(title, str) or len(title.strip()) < 3:
        raise HTTPException(status_code=400, detail="Title must be at least 3 characters")
    if not isinstance(description, str) or len(description.strip()) < 5:
        raise HTTPException(status_code=400, detail="Description must be at least 5 characters")
    if not isinstance(priority, str) or priority.strip() not in VALID_PRIORITY:
        raise HTTPException(status_code=400, detail="Invalid priority")

    return create_ticket(title.strip(), description.strip(), priority.strip())


@app.get("/tickets/metrics/summary")
def ticket_metrics():
    return get_ticket_metrics()


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    ticket = get_ticket_by_id(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.patch("/tickets/{ticket_id}")
def patch_ticket(ticket_id: int, ticket_update: dict):
    title = ticket_update.get("title")
    description = ticket_update.get("description")
    status = ticket_update.get("status")
    priority = ticket_update.get("priority")

    if title is None and description is None and status is None and priority is None:
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    if title is not None:
        if not isinstance(title, str) or len(title.strip()) < 3:
            raise HTTPException(status_code=400, detail="Title must be at least 3 characters")
        title = title.strip()

    if description is not None:
        if not isinstance(description, str) or len(description.strip()) < 5:
            raise HTTPException(status_code=400, detail="Description must be at least 5 characters")
        description = description.strip()

    if status is not None:
        if not isinstance(status, str) or status.strip() not in VALID_STATUS:
            raise HTTPException(status_code=400, detail="Invalid status")
        status = status.strip()

    if priority is not None:
        if not isinstance(priority, str) or priority.strip() not in VALID_PRIORITY:
            raise HTTPException(status_code=400, detail="Invalid priority")
        priority = priority.strip()

    updated_ticket = update_ticket(ticket_id, title, description, status, priority)
    if updated_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return updated_ticket


@app.put("/tickets/{ticket_id}/status")
def put_ticket_status(ticket_id: int, ticket_update: dict):
    status = ticket_update.get("status")

    if not isinstance(status, str) or status.strip() not in VALID_STATUS:
        raise HTTPException(status_code=400, detail="Invalid status")

    updated_ticket = update_ticket_status(ticket_id, status.strip())
    if updated_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return updated_ticket


@app.delete("/tickets/{ticket_id}")
def remove_ticket(ticket_id: int):
    deleted = delete_ticket(ticket_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": f"Ticket {ticket_id} deleted successfully"}
