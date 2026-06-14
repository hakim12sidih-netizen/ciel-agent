"""
CIEL v∞.8 — CONTROL ENGINE.
CIEL agit — souris, clavier, presse-papier, notifications.

Concept : CIEL contrôle la souris (mouvement, clic, drag),
le clavier (frappe, raccourcis), le presse-papier, et envoie
des notifications. Mode démonstration : pas de contrôle réel
sauf si permission explicite.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class ControlAction:
    id: str
    action_type: str  # mouse_move | click | keypress | type | clipboard | notify
    params: dict = field(default_factory=dict)
    timestamp: float = 0.0
    success: bool = False
    simulated: bool = True  # true = pas de vrai contrôle

    def to_dict(self) -> dict:
        return {"id": self.id, "action": self.action_type,
                "simulated": self.simulated,
                "success": self.success}


class ControlEngine:
    """Moteur de contrôle — souris, clavier, presse-papier.

    Toute action est simulée par défaut. Le mode 'live'
    nécessite permission explicite de l'utilisateur.
    """

    def __init__(self):
        self.history: list[ControlAction] = []
        self._live_mode: bool = False
        self._screen_size: tuple[int, int] = (1920, 1080)
        self._clipboard_memory: str = ""
        self.network = LeaderNetwork()

    def set_live_mode(self, enabled: bool):
        self._live_mode = enabled

    def mouse_move(self, x: int, y: int) -> ControlAction:
        action = self._record("mouse_move", {"x": x, "y": y})
        if self._live_mode:
            try:
                import pyautogui
                pyautogui.moveTo(x, y)
                action.success = True
            except ImportError:
                pass
        return action

    def click(self, button: str = "left", x: int | None = None,
              y: int | None = None) -> ControlAction:
        params = {"button": button}
        if x is not None:
            params["x"] = x
        if y is not None:
            params["y"] = y
        action = self._record("click", params)
        if self._live_mode:
            try:
                import pyautogui
                if x is not None and y is not None:
                    pyautogui.click(x, y, button=button)
                else:
                    pyautogui.click(button=button)
                action.success = True
            except ImportError:
                pass
        return action

    def type_text(self, text: str) -> ControlAction:
        action = self._record("type", {"text": text[:50]})
        if self._live_mode:
            try:
                import pyautogui
                pyautogui.write(text)
                action.success = True
            except ImportError:
                pass
        return action

    def keypress(self, key: str) -> ControlAction:
        action = self._record("keypress", {"key": key})
        if self._live_mode:
            try:
                import pyautogui
                pyautogui.press(key)
                action.success = True
            except ImportError:
                pass
        return action

    def clipboard_set(self, text: str) -> ControlAction:
        action = self._record("clipboard", {"text": text[:100]})
        self._clipboard_memory = text
        if self._live_mode:
            try:
                import pyperclip
                pyperclip.copy(text)
                action.success = True
            except ImportError:
                pass
        return action

    def clipboard_get(self) -> str:
        if not self._live_mode:
            return self._clipboard_memory
        try:
            import pyperclip
            return pyperclip.paste()
        except ImportError:
            return self._clipboard_memory or "[pyperclip non installé]"

    def notify(self, title: str, message: str) -> ControlAction:
        action = self._record("notify", {"title": title,
                                          "message": message[:100]})
        try:
            import notifypy
            n = notifypy.Notify()
            n.title = title
            n.message = message
            n.send()
            action.success = True
        except ImportError:
            pass
        return action

    def _record(self, atype: str, params: dict) -> ControlAction:
        a = ControlAction(
            id=f"CTL-{uuid.uuid4().hex[:12]}",
            action_type=atype, params=params,
            timestamp=time.time(), simulated=not self._live_mode,
        )
        self.history.append(a)
        return a

    def get_stats(self) -> dict:
        return {
            "actions": len(self.history),
            "live_mode": self._live_mode,
            "last_action": self.history[-1].action_type
                           if self.history else "none",
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "move":
            a = self.mouse_move(input_data.get("x", 0),
                                input_data.get("y", 0))
            return {"status": "ok", "action": a.to_dict()}
        elif action == "click":
            a = self.click(input_data.get("button", "left"),
                           input_data.get("x"),
                           input_data.get("y"))
            return {"status": "ok", "action": a.to_dict()}
        elif action == "type":
            a = self.type_text(input_data.get("text", ""))
            return {"status": "ok", "action": a.to_dict()}
        elif action == "key":
            a = self.keypress(input_data.get("key", ""))
            return {"status": "ok", "action": a.to_dict()}
        elif action == "clipboard_set":
            a = self.clipboard_set(input_data.get("text", ""))
            return {"status": "ok", "action": a.to_dict()}
        elif action == "clipboard_get":
            return {"status": "ok",
                    "text": self.clipboard_get()}
        elif action == "notify":
            a = self.notify(input_data.get("title", "CIEL"),
                            input_data.get("message", ""))
            return {"status": "ok", "action": a.to_dict()}
        elif action == "live_mode":
            self.set_live_mode(input_data.get("enabled", False))
            return {"status": "ok",
                    "live_mode": self._live_mode}
        return {"status": "ok", "actions": len(self.history)}
