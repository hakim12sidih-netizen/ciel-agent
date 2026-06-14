# `ciel.mesh.node` — Mesh Node

## Classes

### `Any`

Special type indicating an unconstrained type.

- Any is compatible with every type.
- Any assumed to have all methods.
- All values assumed to be instances of Any.

Note that all the above statements are true from the point of view of
static type checkers. At runtime, Any should not be used with instance
checks.

### `GrpcTransport`

**Méthodes :**

- **`__init__(identity: NodeIdentity, discovery: PeerDiscovery, host: str = '0.0.0.0', port: int = 0)`**
- **`announce(peer: PeerInfo)`**
- **`append_entries(peer: PeerInfo, entries: list[dict])`**
- **`gossip(topic: str, payload: bytes, ttl: int = 3, target: str | None = None)`**
- **`on_gossip(cb: Callable)`**
- **`on_peer_connected(cb: Callable)`**
- **`ping(peer: PeerInfo)`**
- **`request_vote(peer: PeerInfo)`**
- **`start()`**
- **`stop()`**

### `LeaderNetwork`

Bus d'événements central de CIEL.

Pattern publish/subscribe avec :
- Filtrage par type d'événement
- Historique des événements
- Métriques de traffic

**Méthodes :**

- **`clear_history()`**
- **`emit(event_type: str, data: dict[str, Any], source: str = 'leader_network')`**
- **`get_history(event_type: str | None = None, limit: int = 50)`**
- **`stats()`**
- **`subscribe(event_type: str, callback: Callable[[Event], None])`**
- **`unsubscribe(token: str)`**

### `MeshNode`

**Méthodes :**

- **`__init__(identity: NodeIdentity | None = None, namespace: str = 'ciel-net', host: str = '0.0.0.0', port: int = 0, data_dir: str | None = None)`**
- **`append_log(command: str, data: dict = None)`**
- **`broadcast_gossip(topic: str, payload: bytes, ttl: int = 3)`**
- **`connect_to(address: str, port: int)`**
- **`find_peer(peer_id: str)`**
- **`get_peers()`**
- **`get_stats()`**
- **`join(seeds: list[str] = None, discover_interval: float = 5.0)`**
- **`process(input_data: dict)`**
- **`save_state()`**
- **`start()`**
- **`start_election()`**
- **`stop()`**

### `NodeIdentity`

NodeIdentity(peer_id: 'str', private_key: 'Ed25519PrivateKey', public_key: 'Ed25519PublicKey', address: 'str' = '', port: 'int' = 0, protocol_version: 'int' = 1, capabilities: 'list[str]' = <factory>, created_at: 'float' = <factory>)

**Méthodes :**

- **`__init__(peer_id: str, private_key: Ed25519PrivateKey, public_key: Ed25519PublicKey, address: str = '', port: int = 0, protocol_version: int = 1, capabilities: list[str] = <factory>, created_at: float = <factory>)`**
- **`save(path: str | Path)`**
- **`sign(data: bytes)`**
- **`to_dict()`**
- **`to_peer_proto()`**
- **`verify(data: bytes, signature: bytes, peer_key: bytes)`**

### `Path`

PurePath subclass that can make system calls.

Path represents a filesystem path but unlike PurePath, also offers
methods to do system calls on path objects. Depending on your system,
instantiating a Path will return either a PosixPath or a WindowsPath
object. You can also instantiate a PosixPath or WindowsPath directly,
but cannot instantiate a WindowsPath on a POSIX system or vice versa.

**Méthodes :**

- **`__init__(args)`**
- **`absolute()`**
  - Return an absolute version of this path
- **`as_posix()`**
  - Return the string representation of the path with forward (/)
- **`as_uri()`**
  - Return the path as a URI.
- **`chmod(mode, follow_symlinks = True)`**
  - Change the permissions of the path, like os.chmod().
- **`copy(target, kwargs)`**
  - Recursively copy this file or directory tree to the given destination.
- **`copy_into(target_dir, kwargs)`**
  - Copy this file or directory tree into the given existing directory.
- **`exists(follow_symlinks = True)`**
  - Whether this path exists.
- **`expanduser()`**
  - Return a new path with expanded ~ and ~user constructs
- **`full_match(pattern, case_sensitive = None)`**
  - Return True if this path matches the given glob-style pattern. The
- **`glob(pattern, case_sensitive = None, recurse_symlinks = False)`**
  - Iterate over this subtree and yield all existing files (of any
- **`group(follow_symlinks = True)`**
  - Return the group name of the file gid.
- **`hardlink_to(target)`**
  - Make this path a hard link pointing to the same file as *target*.
- **`is_absolute()`**
  - True if the path is absolute (has both a root and, if applicable,
- **`is_block_device()`**
  - Whether this path is a block device.
- **`is_char_device()`**
  - Whether this path is a character device.
- **`is_dir(follow_symlinks = True)`**
  - Whether this path is a directory.
- **`is_fifo()`**
  - Whether this path is a FIFO.
- **`is_file(follow_symlinks = True)`**
  - Whether this path is a regular file (also True for symlinks pointing
- **`is_junction()`**
  - Whether this path is a junction.
- **`is_mount()`**
  - Check if this path is a mount point
- **`is_relative_to(other)`**
  - Return True if the path is relative to another path or False.
- **`is_reserved()`**
  - Return True if the path contains one of the special names reserved
- **`is_socket()`**
  - Whether this path is a socket.
- **`is_symlink()`**
  - Whether this path is a symbolic link.
- **`iterdir()`**
  - Yield path objects of the directory contents.
- **`joinpath(pathsegments)`**
  - Combine this path with one or several arguments, and return a
- **`lchmod(mode)`**
  - Like chmod(), except if the path points to a symlink, the symlink's
- **`lstat()`**
  - Like stat(), except if the path points to a symlink, the symlink's
- **`match(path_pattern, case_sensitive = None)`**
  - Return True if this path matches the given pattern. If the pattern is
- **`mkdir(mode = 511, parents = False, exist_ok = False)`**
  - Create a new directory at this given path.
- **`move(target)`**
  - Recursively move this file or directory tree to the given destination.
- **`move_into(target_dir)`**
  - Move this file or directory tree into the given existing directory.
- **`open(mode = 'r', buffering = -1, encoding = None, errors = None, newline = None)`**
  - Open the file pointed to by this path and return a file object, as
- **`owner(follow_symlinks = True)`**
  - Return the login name of the file owner.
- **`read_bytes()`**
  - Open the file in bytes mode, read it, and close the file.
- **`read_text(encoding = None, errors = None, newline = None)`**
  - Open the file in text mode, read it, and close the file.
- **`readlink()`**
  - Return the path to which the symbolic link points.
- **`relative_to(other, walk_up = False)`**
  - Return the relative path to another path identified by the passed
- **`rename(target)`**
  - Rename this path to the target path.
- **`replace(target)`**
  - Rename this path to the target path, overwriting if that path exists.
- **`resolve(strict = False)`**
  - Make the path absolute, resolving all symlinks on the way and also
- **`rglob(pattern, case_sensitive = None, recurse_symlinks = False)`**
  - Recursively yield all existing files (of any kind, including
- **`rmdir()`**
  - Remove this directory.  The directory must be empty.
- **`samefile(other_path)`**
  - Return whether other_path is the same or not as this file
- **`stat(follow_symlinks = True)`**
  - Return the result of the stat() system call on this path, like
- **`symlink_to(target, target_is_directory = False)`**
  - Make this path a symlink pointing to the target path.
- **`touch(mode = 438, exist_ok = True)`**
  - Create this file with the given access mode, if it doesn't exist.
- **`unlink(missing_ok = False)`**
  - Remove this file or link.
- **`walk(top_down = True, on_error = None, follow_symlinks = False)`**
  - Walk the directory tree from this directory, similar to os.walk().
- **`with_name(name)`**
  - Return a new path with the file name changed.
- **`with_segments(pathsegments)`**
  - Construct a new path object from any number of path-like objects.
- **`with_stem(stem)`**
  - Return a new path with the stem changed.
- **`with_suffix(suffix)`**
  - Return a new path with the file suffix changed.  If the path
- **`write_bytes(data)`**
  - Open the file in bytes mode, write to it, and close the file.
- **`write_text(data, encoding = None, errors = None, newline = None)`**
  - Open the file in text mode, write to it, and close the file.

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
