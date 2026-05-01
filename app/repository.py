import sqlite3
from contextlib import closing
from typing import Optional

from app.database import get_connection
from app.schemas import TicketCreate, TicketPriority, TicketStatus, TicketUpdate


def _to_record(row: sqlite3.Row) -> dict:
    return dict(row)


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.strip()


def create_ticket(ticket: TicketCreate) -> dict:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tickets (title, description, status, priority)
            VALUES (?, ?, ?, ?)
            """,
            (
                ticket.title,
                ticket.description,
                TicketStatus.OPEN.value,
                ticket.priority.value,
            ),
        )
        conn.commit()
        ticket_id = cursor.lastrowid

        cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        return _to_record(row)


def list_tickets(
    *,
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    search: Optional[str] = None,
    limit: int,
    offset: int,
) -> list[dict]:
    query = ["SELECT * FROM tickets"]
    filters: list[str] = []
    params: list[object] = []

    if status:
        filters.append("status = ?")
        params.append(status.value)

    if priority:
        filters.append("priority = ?")
        params.append(priority.value)

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
        rows = cursor.fetchall()
        return [_to_record(row) for row in rows]


def get_ticket_by_id(ticket_id: int) -> Optional[dict]:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return _to_record(row)


def update_ticket(ticket_id: int, ticket_update: TicketUpdate) -> Optional[dict]:
    current_ticket = get_ticket_by_id(ticket_id)
    if current_ticket is None:
        return None

    updated_title = _clean_optional_text(ticket_update.title)
    updated_description = _clean_optional_text(ticket_update.description)

    title = updated_title if updated_title is not None else current_ticket["title"]
    description = (
        updated_description
        if updated_description is not None
        else current_ticket["description"]
    )
    status = ticket_update.status.value if ticket_update.status else current_ticket["status"]
    priority = (
        ticket_update.priority.value if ticket_update.priority else current_ticket["priority"]
    )

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
        row = cursor.fetchone()
        return _to_record(row)


def update_ticket_status(ticket_id: int, status: TicketStatus) -> Optional[dict]:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tickets WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        if row is None:
            return None

        cursor.execute(
            """
            UPDATE tickets
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status.value, ticket_id),
        )
        conn.commit()
        cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        updated_row = cursor.fetchone()
        return _to_record(updated_row)


def delete_ticket(ticket_id: int) -> bool:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tickets WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        if row is None:
            return False

        cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
        conn.commit()
        return True


def get_ticket_metrics() -> dict:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END), 0) AS open,
                COALESCE(SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END), 0) AS in_progress,
                COALESCE(SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END), 0) AS resolved,
                COALESCE(SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END), 0) AS closed
            FROM tickets
            """
        )
        row = cursor.fetchone()
        return dict(row)
