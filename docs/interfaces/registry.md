# `ciel.interfaces.backends.registry` — Registry

## Classes

### `Any`

Special type indicating an unconstrained type.

- Any is compatible with every type.
- Any assumed to have all methods.
- All values assumed to be instances of Any.

Note that all the above statements are true from the point of view of
static type checkers. At runtime, Any should not be used with instance
checks.

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

## Fonctions

### `get(mode: str)`

### `get_all()`

### `get_available()`

### `get_stats()`

### `get_terminal_adapters()`

### `load_default_backends()`

### `register(backend: InterfaceBackend)`
