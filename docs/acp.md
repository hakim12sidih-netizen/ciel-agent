# `ciel.acp` — Agent Communication Protocol

## Constantes

- **`CIEL_TOOLS`** (`list`) — `[ACPTool(name='ciel_chat', description='Envoie un message à CIEL et reçoit une réponse LLM', input_schema={'type': 'obje`
- **`CODE_TOOLS`** (`list`) — `[ACPTool(name='analyze_code', description="Analyse un fichier source et retourne des suggestions d'amélioration, bugs, e`

## Classes

### `ACPAgent`

ACPAgent(agent_id: 'str', name: 'str', description: 'str' = '', capabilities: 'list[str]' = <factory>, tools: 'list[str]' = <factory>, resources: 'list[str]' = <factory>)

**Méthodes :**

- **`__init__(agent_id: str, name: str, description: str = '', capabilities: list[str] = <factory>, tools: list[str] = <factory>, resources: list[str] = <factory>)`**
- **`to_dict()`**

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

### `ACPServer`

**Méthodes :**

- **`__init__(host: str = '127.0.0.1', ws_port: int = 9876)`**
- **`get_stats()`**
- **`register_resource_handler(uri: str, handler: Callable)`**
- **`register_tool_handler(tool_name: str, handler: Callable)`**
- **`serve_stdio()`**
- **`start()`**
- **`stop()`**

### `ACPTool`

ACPTool(name: 'str', description: 'str', input_schema: 'dict[str, Any]', handler: 'str' = '', scope: 'ACPScope' = <ACPScope.PUBLIC: 'public'>, categories: 'list[str]' = <factory>)

**Méthodes :**

- **`__init__(name: str, description: str, input_schema: dict[str, Any], handler: str = '', scope: ACPScope = <ACPScope.PUBLIC: 'public'>, categories: list[str] = <factory>)`**
- **`to_dict()`**

## Fonctions

### `generate_cursor_rules(target_dir: str)`

### `generate_vscode_extension(target_dir: str)`

### `get_all_tools()`

### `get_tools_by_category(category: str)`

## Exportations

- `ACPServer`
- `ACPTool`
- `ACPResource`
- `ACPPrompt`
- `ACPAgent`
- `ACPScope`
- `get_all_tools`
- `get_tools_by_category`
- `CODE_TOOLS`
- `CIEL_TOOLS`
- `generate_vscode_extension`
- `generate_cursor_rules`
