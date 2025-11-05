"""Unit tests for trello_client_api.models conversion helpers."""

from types import SimpleNamespace

from trello_client_api.models import TrelloBoard, TrelloCard, TrelloList, TrelloUser


def test_from_generated_helpers_cover_all_models() -> None:
    """from_generated should safely convert plain objects into models."""
    board_src = SimpleNamespace(id="b1", name="B", description="d", closed=False, url="u")
    list_src = SimpleNamespace(id="l1", name="L", board_id="b1", position=1.0, closed=False)
    card_src = SimpleNamespace(
        id="c1",
        name="C",
        list_id="l1",
        board_id="b1",
        description="dd",
        position=0.0,
        closed=False,
        url="u",
    )
    user_src = SimpleNamespace(id="u1", username="alice", full_name="Alice", email="a@example.com")

    board = TrelloBoard.from_generated(board_src)
    tlist = TrelloList.from_generated(list_src)
    card = TrelloCard.from_generated(card_src)
    user = TrelloUser.from_generated(user_src)

    assert board.id == "b1" and board.name == "B"
    assert tlist.id == "l1" and tlist.board_id == "b1"
    assert card.id == "c1" and card.list_id == "l1" and card.board_id == "b1"
    assert user.username == "alice"


