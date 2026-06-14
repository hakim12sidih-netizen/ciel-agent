# `ciel.acp.tools` — Outils ACP

## Constantes

- **`CIEL_TOOLS`** (`list`) — `[ACPTool(name='ciel_chat', description='Envoie un message à CIEL et reçoit une réponse LLM', input_schema={'type': 'obje`
- **`CODE_TOOLS`** (`list`) — `[ACPTool(name='analyze_code', description="Analyse un fichier source et retourne des suggestions d'amélioration, bugs, e`
- **`TOOL_HANDLERS`** (`dict`) — `{'analyze_code': <function handle_analyze_code at 0x7f41efbdc3b0>, 'search_code': <function handle_search_code at 0x7f41`

## Classes

### `ACPScope`

### `ACPTool`

ACPTool(name: 'str', description: 'str', input_schema: 'dict[str, Any]', handler: 'str' = '', scope: 'ACPScope' = <ACPScope.PUBLIC: 'public'>, categories: 'list[str]' = <factory>)

**Méthodes :**

- **`__init__(name: str, description: str, input_schema: dict[str, Any], handler: str = '', scope: ACPScope = <ACPScope.PUBLIC: 'public'>, categories: list[str] = <factory>)`**
- **`to_dict()`**

### `Any`

Special type indicating an unconstrained type.

- Any is compatible with every type.
- Any assumed to have all methods.
- All values assumed to be instances of Any.

Note that all the above statements are true from the point of view of
static type checkers. At runtime, Any should not be used with instance
checks.

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

## Fonctions

### `get_all_tools()`

### `get_tools_by_category(category: str)`

### `handle_analyze_code(file_path: str, language: str | None = None, kwargs)`

### `handle_list_directory(path: str, recursive: bool = False, kwargs)`

### `handle_read_file(file_path: str, offset: int | None = None, limit: int | None = None, kwargs)`

### `handle_run_command(command: str, workdir: str | None = None, timeout: int = 30, kwargs)`

### `handle_search_code(pattern: str, path: str | None = None, file_pattern: str | None = None, max_results: int = 50, kwargs)`

### `handle_write_file(file_path: str, content: str, kwargs)`
