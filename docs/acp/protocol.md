# `ciel.acp.protocol` — Protocol (JSON-RPC 2.0)

## Constantes

- **`ACP_CAPABILITIES`** (`dict`) — `{'tools': {'listChanged': True}, 'resources': {'subscribe': True, 'listChanged': True}, 'prompts': {'listChanged': True}`
- **`ACP_PROTOCOL_VERSION`** (`str`) — `'2026-06-14'`
- **`ACP_SERVER_INFO`** (`dict`) — `{'name': 'ciel-acp', 'version': '1.0.0'}`
- **`REQUESTS_TO_CATCH_UP`** (`str`) — `'requests-to-catch-up'`

## Classes

### `ACPAgent`

ACPAgent(agent_id: 'str', name: 'str', description: 'str' = '', capabilities: 'list[str]' = <factory>, tools: 'list[str]' = <factory>, resources: 'list[str]' = <factory>)

**Méthodes :**

- **`__init__(agent_id: str, name: str, description: str = '', capabilities: list[str] = <factory>, tools: list[str] = <factory>, resources: list[str] = <factory>)`**
- **`to_dict()`**

### `ACPMessageType`

### `ACPPrompt`

ACPPrompt(name: 'str', description: 'str', arguments: 'list[dict]' = <factory>)

**Méthodes :**

- **`__init__(name: str, description: str, arguments: list[dict] = <factory>)`**
- **`to_dict()`**

### `ACPResource`

ACPResource(uri: 'str', name: 'str', description: 'str' = '', mime_type: 'str' = 'text/plain', handler: 'str' = '')

**Méthodes :**

- **`__init__(uri: str, name: str, description: str = '', mime_type: str = 'text/plain', handler: str = '')`**
- **`to_dict()`**

### `ACPScope`

### `ACPTool`

ACPTool(name: 'str', description: 'str', input_schema: 'dict[str, Any]', handler: 'str' = '', scope: 'ACPScope' = <ACPScope.PUBLIC: 'public'>, categories: 'list[str]' = <factory>)

**Méthodes :**

- **`__init__(name: str, description: str, input_schema: dict[str, Any], handler: str = '', scope: ACPScope = <ACPScope.PUBLIC: 'public'>, categories: list[str] = <factory>)`**
- **`to_dict()`**

### `ACPVersion`

### `Any`

Special type indicating an unconstrained type.

- Any is compatible with every type.
- Any assumed to have all methods.
- All values assumed to be instances of Any.

Note that all the above statements are true from the point of view of
static type checkers. At runtime, Any should not be used with instance
checks.

### `Enum`

Create a collection of name/value pairs.

Example enumeration:

>>> class Color(Enum):
...     RED = 1
...     BLUE = 2
...     GREEN = 3

Access them by:

- attribute access:

>>> Color.RED
<Color.RED: 1>

- value lookup:

>>> Color(1)
<Color.RED: 1>

- name lookup:

>>> Color['RED']
<Color.RED: 1>

Enumerations can be iterated over, and know how many members they have:

>>> len(Color)
3

>>> list(Color)
[<Color.RED: 1>, <Color.BLUE: 2>, <Color.GREEN: 3>]

Methods can be added to enumerations, and members can have their own
attributes -- see the documentation for details.

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
