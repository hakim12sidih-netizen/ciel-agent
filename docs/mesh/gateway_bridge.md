# `ciel.mesh.gateway_bridge` — Gateway Bridge

## Classes

### `Any`

Special type indicating an unconstrained type.

- Any is compatible with every type.
- Any assumed to have all methods.
- All values assumed to be instances of Any.

Note that all the above statements are true from the point of view of
static type checkers. At runtime, Any should not be used with instance
checks.

### `GatewayBridge`

Pont entre le MeshNode distribué et le Gateway CIEL.

Enregistre des handlers d'événements sur le LeaderNetwork
pour que les événements du mesh soient dispatchables via
le Gateway (methodes mesh.*).

**Méthodes :**

- **`__init__(mesh: MeshNode)`**
- **`register_gateway_methods(gateway: Any)`**
  - Enregistre les méthodes mesh.* sur une instance GatewayServer.
- **`subscribe_events()`**

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
