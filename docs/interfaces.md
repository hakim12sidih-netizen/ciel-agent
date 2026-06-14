# `ciel.interfaces` — Interfaces — Backends, Capabilities, Thèmes

Transverse — INTERFACES : 6 modes d'interaction avec l'extérieur.
  - cli, tui, voice, canvas, api_server, acp

---

## Classes

### `InterfacesEngine`

Moteur d'interfaces — 6 modes de communication avec l'extérieur.

**Méthodes :**

- **`__init__()`**
- **`close_session(session_id: str)`**
- **`create_session(mode: str, metadata: Any)`**
- **`get_stats()`**
- **`process(input_data: Any)`**

### `TerminalCapabilityDetector`

**Méthodes :**

- **`__init__()`**
- **`color_depth()`**
- **`detect(force: bool = False)`**
- **`emulator()`**
- **`features()`**
- **`has_capability(cap: str)`**
- **`protocol()`**
- **`supports_images()`**
- **`supports_true_color()`**
- **`supports_unicode()`**
- **`to_dict()`**

## Fonctions

### `get_detector()`

### `get_theme(name: str | None = None)`

### `list_themes()`

### `set_theme(name: str)`

## Exportations

- `InterfacesEngine`
- `cli`
- `get_detector`
- `TerminalCapabilityDetector`
- `get_theme`
- `set_theme`
- `list_themes`
