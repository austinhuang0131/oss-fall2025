from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MessageResponse")


@_attrs_define
class MessageResponse:
    """Represents an email message response.

    Example:
        {'body': 'This is a test message body', 'date': '2025-10-03', 'from': 'sender@example.com', 'id': 'msg_123',
            'subject': 'Test Message', 'to': 'recipient@example.com'}

    Attributes:
        id (str): Unique identifier of the message
        from_ (str): Sender's email address
        to (str): Recipient's email address
        date (str): Date the message was sent
        subject (str): Subject line of the message
        body (Union[Unset, str]): Body content of the message Default: ''.
    """

    id: str
    from_: str
    to: str
    date: str
    subject: str
    body: Union[Unset, str] = ""
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        from_ = self.from_

        to = self.to

        date = self.date

        subject = self.subject

        body = self.body

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "from": from_,
                "to": to,
                "date": date,
                "subject": subject,
            }
        )
        if body is not UNSET:
            field_dict["body"] = body

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        from_ = d.pop("from")

        to = d.pop("to")

        date = d.pop("date")

        subject = d.pop("subject")

        body = d.pop("body", UNSET)

        message_response = cls(
            id=id,
            from_=from_,
            to=to,
            date=date,
            subject=subject,
            body=body,
        )

        message_response.additional_properties = d
        return message_response

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
