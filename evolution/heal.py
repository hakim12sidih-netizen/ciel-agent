from __future__ import annotations

import os
import shutil
import time
from typing import Any, Callable


class Heal:
    def __init__(
        self,
        llm_complete_fn: Callable[[str], str] | None = None,
        verify_fn: Callable[[str, str], bool] | None = None,
    ) -> None:
        self._llm_complete = llm_complete_fn
        self._verify_fn = verify_fn
        self._heal_history: dict[str, int] = {}

    def diagnose_and_repair(self, target_file: str, error: str) -> bool:
        if not os.path.isfile(target_file):
            return False
        try:
            with open(target_file, encoding="utf-8") as f:
                original_code = f.read()
        except OSError:
            return False

        if self._llm_complete is None:
            return False

        prompt = (
            f"System Failure detected in {target_file}. Error: {error}\n\n"
            f"Original Code:\n{original_code}\n\n"
            f"Task: REPAIR the code to fix this specific bug. Return ONLY the corrected code."
        )
        repaired_code = self._llm_complete(prompt)
        if not repaired_code:
            return False

        if self._verify_fn is not None and not self._verify_fn(target_file, repaired_code):
            return False

        backup_path = target_file + ".bak"
        try:
            shutil.copy2(target_file, backup_path)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(repaired_code)
        except OSError:
            return False

        self._heal_history[target_file] = self._heal_history.get(target_file, 0) + 1
        return True

    def get_stats(self) -> list[tuple[str, int]]:
        return list(self._heal_history.items())

    def process(self, input_data: Any) -> dict[str, Any]:
        if isinstance(input_data, dict):
            target = input_data.get("target_file", "")
            error = input_data.get("error", "")
            if target and error:
                success = self.diagnose_and_repair(target, error)
                return {"repaired": success, "target": target}
        return {"history": dict(self._heal_history)}
