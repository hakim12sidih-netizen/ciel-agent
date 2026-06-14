# `ciel.interfaces.backends.voice_backend` — Backend Voice

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

### `VoiceBackend`

**Méthodes :**

- **`__init__()`**
- **`close_session(session_id: str)`**
- **`create_session(metadata)`**
- **`get_sessions()`**
- **`get_stats()`**
- **`is_available()`**
- **`start()`**
- **`stop()`**
- **`terminal_info()`**
