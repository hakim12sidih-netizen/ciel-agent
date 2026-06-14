# `ciel.mesh.discovery` — Peer Discovery

## Classes

### `Any`

Special type indicating an unconstrained type.

- Any is compatible with every type.
- Any assumed to have all methods.
- All values assumed to be instances of Any.

Note that all the above statements are true from the point of view of
static type checkers. At runtime, Any should not be used with instance
checks.

### `PeerDiscovery`

**Méthodes :**

- **`__init__(peer_id: str, namespace: str = 'ciel-net')`**
- **`active_peers(timeout: float = 60.0)`**
- **`add_peer(info: PeerInfo)`**
- **`all_peers()`**
- **`get_peer(peer_id: str)`**
- **`on_peer_added(cb: Callable)`**
- **`on_peer_removed(cb: Callable)`**
- **`peer_count()`**
- **`peers_by_role(role: str)`**
- **`prune_stale(timeout: float = 300.0)`**
- **`register_seed(address: str)`**
- **`remove_peer(peer_id: str)`**
- **`seeds()`**
- **`to_dict()`**

### `PeerInfo`

PeerInfo(peer_id: 'str', address: 'str' = '', port: 'int' = 0, role: 'str' = 'ouvriere', state: 'int' = 0, public_key: 'str' = '', protocol_version: 'int' = 1, capabilities: 'list[str]' = <factory>, last_seen: 'float' = 0.0, latency: 'float' = 0.0, trust_score: 'float' = 0.5, first_seen: 'float' = 0.0)

**Méthodes :**

- **`__init__(peer_id: str, address: str = '', port: int = 0, role: str = 'ouvriere', state: int = 0, public_key: str = '', protocol_version: int = 1, capabilities: list[str] = <factory>, last_seen: float = 0.0, latency: float = 0.0, trust_score: float = 0.5, first_seen: float = 0.0)`**
- **`is_active(timeout: float = 60.0)`**

## Fonctions

### `dataclass(cls = None, init = True, repr = True, eq = True, order = False, unsafe_hash = False, frozen = False, match_args = True, kw_only = False, slots = False, weakref_slot = False)`

Add dunder methods based on the fields defined in the class.

Examines PEP 526 __annotations__ to determine fields.

If init is true, an __init__() method is added to the class. If repr
is true, a __repr__() method is added. If order is true, rich
comparison dunder methods are added. If unsafe_hash is true, a
__hash__() method is added. If frozen is true, fields may not be
assigned to after instance creation. If match_args is true, the
__match_args__ tuple is added. If kw_only is true, then by default
all fields are keyword-only. If slots is true, a new class with a
__slots__ attribute is returned.

### `field(default = <dataclasses._MISSING_TYPE object at 0x7f41f5162cf0>, default_factory = <dataclasses._MISSING_TYPE object at 0x7f41f5162cf0>, init = True, repr = True, hash = None, compare = True, metadata = None, kw_only = <dataclasses._MISSING_TYPE object at 0x7f41f5162cf0>, doc = None)`

Return an object to identify dataclass fields.

default is the default value of the field.  default_factory is a
0-argument function called to initialize a field's value.  If init
is true, the field will be a parameter to the class's __init__()
function.  If repr is true, the field will be included in the
object's repr().  If hash is true, the field will be included in the
object's hash().  If compare is true, the field will be used in
comparison functions.  metadata, if specified, must be a mapping
which is stored but not otherwise examined by dataclass.  If kw_only
is true, the field will become a keyword-only parameter to
__init__().  doc is an optional docstring for this field.

It is an error to specify both default and default_factory.
