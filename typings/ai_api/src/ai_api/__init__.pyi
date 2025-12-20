from abc import ABC, abstractmethod
from typing import Any

class AIInterface(ABC):
    @abstractmethod
    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, Any] | None = ...,
    ) -> str | dict[str, Any]:
        ...
