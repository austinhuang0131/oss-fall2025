from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="KanbanList")


@_attrs_define
class KanbanList:
    """Represents a Kanban list within a board.

    Attributes:
        id (str):
        name (str):
        board_id (str):
        position (float):
        closed (bool | Unset):  Default: False.
    """

    id: str
    name: str
    board_id: str
    position: float
    closed: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        board_id = self.board_id

        position = self.position

        closed = self.closed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "board_id": board_id,
                "position": position,
            }
        )
        if closed is not UNSET:
            field_dict["closed"] = closed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        board_id = d.pop("board_id")

        position = d.pop("position")

        closed = d.pop("closed", UNSET)

        kanban_list = cls(
            id=id,
            name=name,
            board_id=board_id,
            position=position,
            closed=closed,
        )

        kanban_list.additional_properties = d
        return kanban_list

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
