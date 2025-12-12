from abc import ABC, abstractmethod

"""Abstract interfaces for Chat APIs."""
class Message(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        ...

    @property
    @abstractmethod
    def content(self) -> str:
        ...

    @property
    @abstractmethod
    def sender_id(self) -> str:
        ...

class ChatInterface(ABC):
    @abstractmethod
    def send_message(self, channel_id: str, content: str) -> bool:
        ...

    @abstractmethod
    def get_messages(self, channel_id: str, limit: int = ...) -> list[Message]:
        ...

    @abstractmethod
    def delete_message(self, channel_id: str, message_id: str) -> bool:
        ...
