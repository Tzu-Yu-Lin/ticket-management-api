from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from app.config import get_settings
from app.database import check_database_health, init_db
from app.repository import (
    create_ticket,
    delete_ticket,
    get_ticket_by_id,
    get_ticket_metrics,
    list_tickets,
    update_ticket,
    update_ticket_status,
)
from app.schemas import (
    DeleteResponse,
    HealthResponse,
    TicketCreate,
    TicketMetricsResponse,
    TicketPriority,
    TicketResponse,
    TicketStatus,
    TicketStatusUpdate,
    TicketUpdate,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict:
    return {
        "message": "Ticket Management API is running",
        "version": settings.app_version,
        "docs_url": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    database_ok = check_database_health()
    return HealthResponse(
        status="ok" if database_ok else "degraded",
        database="connected" if database_ok else "unavailable",
    )


@app.get("/tickets", response_model=list[TicketResponse], tags=["tickets"])
def get_tickets(
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    search: Optional[str] = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    return list_tickets(
        status=status,
        priority=priority,
        search=search,
        limit=limit,
        offset=offset,
    )


@app.post("/tickets", response_model=TicketResponse, status_code=201, tags=["tickets"])
def create_new_ticket(ticket: TicketCreate) -> dict:
    return create_ticket(ticket)


@app.get("/tickets/metrics/summary", response_model=TicketMetricsResponse, tags=["tickets"])
def ticket_metrics() -> dict:
    return get_ticket_metrics()


@app.get("/tickets/{ticket_id}", response_model=TicketResponse, tags=["tickets"])
def get_ticket(ticket_id: int) -> dict:
    ticket = get_ticket_by_id(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.patch("/tickets/{ticket_id}", response_model=TicketResponse, tags=["tickets"])
def patch_ticket(ticket_id: int, ticket_update: TicketUpdate) -> dict:
    if not any(
        [
            ticket_update.title is not None,
            ticket_update.description is not None,
            ticket_update.status is not None,
            ticket_update.priority is not None,
        ]
    ):
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    updated_ticket = update_ticket(ticket_id, ticket_update)
    if updated_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return updated_ticket


@app.put("/tickets/{ticket_id}/status", response_model=TicketResponse, tags=["tickets"])
def put_ticket_status(ticket_id: int, ticket_update: TicketStatusUpdate) -> dict:
    updated_ticket = update_ticket_status(ticket_id, ticket_update.status)
    if updated_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return updated_ticket


@app.delete("/tickets/{ticket_id}", response_model=DeleteResponse, tags=["tickets"])
def remove_ticket(ticket_id: int) -> DeleteResponse:
    deleted = delete_ticket(ticket_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return DeleteResponse(message=f"Ticket {ticket_id} deleted successfully")
