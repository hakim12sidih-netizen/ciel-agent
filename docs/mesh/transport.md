# `ciel.mesh.transport` — Transport gRPC

## Classes

### `AnnounceRequest`

### `AnnounceResponse`

### `Any`

Special type indicating an unconstrained type.

- Any is compatible with every type.
- Any assumed to have all methods.
- All values assumed to be instances of Any.

Note that all the above statements are true from the point of view of
static type checkers. At runtime, Any should not be used with instance
checks.

### `AppendEntriesRequest`

### `AppendEntriesResponse`

### `FindPeerRequest`

### `FindPeerResponse`

### `GossipAck`

### `GossipMessage`

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

### `MeshEnvelope`

### `MeshServiceServicer`

Missing associated documentation comment in .proto file.

**Méthodes :**

- **`Announce(request, context)`**
  - Missing associated documentation comment in .proto file.
- **`AppendEntries(request, context)`**
  - Missing associated documentation comment in .proto file.
- **`FindPeer(request, context)`**
  - Missing associated documentation comment in .proto file.
- **`Gossip(request, context)`**
  - Gossip
- **`PBFTCommit(request, context)`**
  - Missing associated documentation comment in .proto file.
- **`PBFTPrePrepare(request, context)`**
  - PBFT Consensus
- **`PBFTPrepare(request, context)`**
  - Missing associated documentation comment in .proto file.
- **`Ping(request, context)`**
  - Discovery & Heartbeat
- **`RequestVote(request, context)`**
  - Raft Consensus
- **`StreamMessages(request_iterator, context)`**
  - Missing associated documentation comment in .proto file.
- **`SyncState(request, context)`**
  - Data Sync

### `MeshServiceStub`

Missing associated documentation comment in .proto file.

**Méthodes :**

- **`__init__(channel)`**
  - Constructor.

### `MeshServicer`

**Méthodes :**

- **`Announce(request: AnnounceRequest, context)`**
- **`AppendEntries(request: AppendEntriesRequest, context)`**
- **`FindPeer(request: FindPeerRequest, context)`**
- **`Gossip(request: GossipMessage, context)`**
- **`PBFTCommit(request: PBFTMessage, context)`**
- **`PBFTPrePrepare(request: PBFTMessage, context)`**
- **`PBFTPrepare(request: PBFTMessage, context)`**
- **`Ping(request: PingRequest, context)`**
- **`RequestVote(request: RequestVoteRequest, context)`**
- **`StreamMessages(request_iterator, context)`**
- **`SyncState(request: SyncRequest, context)`**
- **`__init__(node: GrpcTransport)`**

### `NodeIdentity`

NodeIdentity(peer_id: 'str', private_key: 'Ed25519PrivateKey', public_key: 'Ed25519PublicKey', address: 'str' = '', port: 'int' = 0, protocol_version: 'int' = 1, capabilities: 'list[str]' = <factory>, created_at: 'float' = <factory>)

**Méthodes :**

- **`__init__(peer_id: str, private_key: Ed25519PrivateKey, public_key: Ed25519PublicKey, address: str = '', port: int = 0, protocol_version: int = 1, capabilities: list[str] = <factory>, created_at: float = <factory>)`**
- **`save(path: str | Path)`**
- **`sign(data: bytes)`**
- **`to_dict()`**
- **`to_peer_proto()`**
- **`verify(data: bytes, signature: bytes, peer_key: bytes)`**

### `PBFTMessage`

### `PBFTResponse`

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

### `PingRequest`

### `PongResponse`

### `RequestVoteRequest`

### `RequestVoteResponse`

### `SyncRequest`

### `SyncResponse`

## Fonctions

### `add_MeshServiceServicer_to_server(servicer, server)`
