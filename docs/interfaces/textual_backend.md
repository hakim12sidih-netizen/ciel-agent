# `ciel.interfaces.backends.textual_backend` — Backend Textual TUI

## Classes

### `InterfaceBackend`

Abstract base class for all interface backends.

A backend is an interface mode (CLI, TUI, Web, Voice, etc.)
with a lifecycle, session management, and terminal-specific
adaptation.

**Méthodes :**

- **`__init__(name: str, mode: str)`**
- **`close_session(session_id: str)`**
- **`create_session(metadata)`**
- **`get_sessions()`**
- **`get_stats()`**
- **`is_available()`**
- **`start()`** *(abstract)*
- **`stop()`** *(abstract)*
- **`terminal_info()`**

### `TextualBackend`

**Méthodes :**

- **`__init__()`**
- **`close_session(session_id: str)`**
- **`create_session(metadata)`**
- **`get_sessions()`**
- **`get_stats()`**
- **`is_available()`**
- **`launch(args: list[str] | None = None)`**
  - Lance l'application Textual TUI.
- **`start()`**
- **`stop()`**
- **`terminal_info()`**
