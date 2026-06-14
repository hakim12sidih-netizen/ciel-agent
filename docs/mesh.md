# `ciel.mesh` — Module Mesh Distribué (gRPC+QUIC)

## Classes

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

### `SwarmAdapter`

Connecte le MeshNode distribué (gRPC+QUIC) au SwarmEngine existant.

Remplace les simulations in-memory du SwarmEngine par le vrai
transport réseau MeshNode. SwarmEngine conserve son interface
publique — l'adapter se charge de la traduction.

**Méthodes :**

- **`__init__(mesh: MeshNode, swarm: SwarmEngine | None = None)`**
- **`process(input_data: dict)`**
- **`raft_append(command: str, data: dict[str, Any] = None)`**
- **`raft_elect()`**
- **`send_message(target: str, content: str, msg_type: str = 'data')`**
- **`sync_peers_to_swarm()`**
  - Synchronise les pairs découverts via le mesh vers le SwarmEngine.

## Exportations

- `MeshNode`
- `NodeIdentity`
- `PeerDiscovery`
- `PeerInfo`
- `GrpcTransport`
- `SwarmAdapter`
- `GatewayBridge`
