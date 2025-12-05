"""Helper functions to convert ABC objects to JSON-serializable dicts."""
from kanban_client_api.models import KanbanBoard, KanbanCard, KanbanList, KanbanUser
from ticket_api.models import Ticket


def board_to_dict(board: KanbanBoard) -> dict[str, str | bool | None]:
    """Convert KanbanBoard ABC to dictionary."""
    return {
        "id": board.id,
        "name": board.name,
        "description": board.description,
        "closed": board.closed,
        "url": board.url,
        "created_at": board.created_at.isoformat() if board.created_at else None,
    }


def list_to_dict(lst: KanbanList) -> dict[str, str | float | bool]:
    """Convert KanbanList ABC to dictionary."""
    return {
        "id": lst.id,
        "name": lst.name,
        "board_id": lst.board_id,
        "position": lst.position,
        "closed": lst.closed,
    }


def card_to_dict(card: KanbanCard) -> dict[str, str | float | bool | None]:
    """Convert KanbanCard ABC to dictionary."""
    return {
        "id": card.id,
        "name": card.name,
        "list_id": card.list_id,
        "board_id": card.board_id,
        "description": card.description,
        "position": card.position,
        "closed": card.closed,
        "due_date": card.due_date.isoformat() if card.due_date else None,
        "url": card.url,
        "created_at": card.created_at.isoformat() if card.created_at else None,
    }


def user_to_dict(user: KanbanUser) -> dict[str, str | None]:
    """Convert KanbanUser ABC to dictionary."""
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
    }


def ticket_to_dict(ticket: Ticket) -> dict[str, str | bool]:
    """Convert Ticket ABC to dictionary."""
    return {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
    }
