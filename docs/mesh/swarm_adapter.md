# `ciel.mesh.swarm_adapter` — Swarm Adapter

## Classes

### `Any`

Special type indicating an unconstrained type.

- Any is compatible with every type.
- Any assumed to have all methods.
- All values assumed to be instances of Any.

Note that all the above statements are true from the point of view of
static type checkers. At runtime, Any should not be used with instance
checks.

### `ConsensusEntry`

ConsensusEntry(term: 'int' = 0, index: 'int' = 0, command: 'str' = '', data: 'dict[str, Any]' = <factory>)

**Méthodes :**

- **`__init__(term: int = 0, index: int = 0, command: str = '', data: dict[str, Any] = <factory>)`**

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

### `Message`

Message(sender: 'str', content: 'str', msg_type: 'str' = 'data', timestamp: 'float' = 0.0, signature: 'str' = '', ttl: 'int' = 3)

**Méthodes :**

- **`__init__(sender: str, content: str, msg_type: str = 'data', timestamp: float = 0.0, signature: str = '', ttl: int = 3)`**

### `ModelUpdate`

ModelUpdate(peer_id: 'str', weights: 'list[float]' = <factory>, n_samples: 'int' = 0, accuracy: 'float' = 0.0)

**Méthodes :**

- **`__init__(peer_id: str, weights: list[float] = <factory>, n_samples: int = 0, accuracy: float = 0.0)`**

### `PeerState`

### `Role`

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

### `SwarmEngine`

Point d'entrée principal — SWARM : Fédération & Civilisation CIEL.

Couvre la découverte de pairs (DHT/mDNS), le transport sécurisé
(Noise XX + Double Ratchet), le consensus distribué (Raft, PBFT),
et l'apprentissage fédéré (FedAvg, SCAFFOLD, Ditto).

**Méthodes :**

- **`__init__(peer_id: str = '', namespace: str = 'ciel-net')`**
- **`federated_round(updates: list[ModelUpdate])`**
- **`get_stats()`**
- **`join(seed_address: str = '')`**
- **`pbft_propose(request: dict[str, Any])`**
- **`process(input_data: Any)`**
- **`raft_append(command: str, data: dict[str, Any] = None)`**
- **`raft_elect()`**
- **`receive_message(msg: Message)`**
- **`send_message(target: str, content: str, msg_type: str = 'data')`**
- **`set_role(role: Role)`**

### `SwarmPeer`

Peer(peer_id: 'str', address: 'str' = '', role: 'Role' = <Role.OUVRIERE: 'ouvriere'>, state: 'PeerState' = <PeerState.OFFLINE: 0>, public_key: 'str' = '', last_seen: 'float' = 0.0, latency: 'float' = 0.0, trust_score: 'float' = 0.5)

**Méthodes :**

- **`__init__(peer_id: str, address: str = '', role: Role = <Role.OUVRIERE: 'ouvriere'>, state: PeerState = <PeerState.OFFLINE: 0>, public_key: str = '', last_seen: float = 0.0, latency: float = 0.0, trust_score: float = 0.5)`**
