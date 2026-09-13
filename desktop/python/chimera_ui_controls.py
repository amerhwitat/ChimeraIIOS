"""Framework-neutral UI control dispatcher for Chimera II applications."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass(frozen=True)
class UIControl:
    control_id: str
    kind: str
    command: str
    arguments: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

class UICommandRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register(self, command: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        if not command or not callable(handler):
            raise ValueError("command and callable handler are required")
        self._handlers[command] = handler

    def dispatch(self, control: UIControl) -> Any:
        if not control.enabled:
            raise RuntimeError(f"UI control disabled: {control.control_id}")
        handler = self._handlers.get(control.command)
        if handler is None:
            raise KeyError(f"No application logic registered for {control.command}")
        return handler(control.arguments)

__all__ = ["UIControl", "UICommandRegistry"]
