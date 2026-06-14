# `ciel.interfaces.backends.base` — Base ABC

## Classes

### `ABC`

Helper class that provides a standard way to create an ABC using
inheritance.

### `Any`

Special type indicating an unconstrained type.

- Any is compatible with every type.
- Any assumed to have all methods.
- All values assumed to be instances of Any.

Note that all the above statements are true from the point of view of
static type checkers. At runtime, Any should not be used with instance
checks.

### `BackendSession`

BackendSession(session_id: 'str', mode: 'str', terminal_emulator: 'str' = '', metadata: 'dict[str, Any]' = <factory>, active: 'bool' = True)

**Méthodes :**

- **`__init__(session_id: str, mode: str, terminal_emulator: str = '', metadata: dict[str, Any] = <factory>, active: bool = True)`**

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

### `abstractmethod(funcobj)`

A decorator indicating abstract methods.

Requires that the metaclass is ABCMeta or derived from it.  A
class that has a metaclass derived from ABCMeta cannot be
instantiated unless all of its abstract methods are overridden.
The abstract methods can be called using any of the normal
'super' call mechanisms.  abstractmethod() may be used to declare
abstract methods for properties and descriptors.

Usage:

class C(metaclass=ABCMeta):
@abstractmethod
def my_abstract_method(self, arg1, arg2, argN):
...

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

### `get_detector()`
