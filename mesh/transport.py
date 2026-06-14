from __future__ import annotations

import json
import logging
import queue
import threading
import time
import uuid
from concurrent import futures
from typing import Any, Callable

import grpc

from .identity import NodeIdentity
from .discovery import PeerInfo, PeerDiscovery
from .proto import (
    MeshServiceStub, MeshServiceServicer,
    add_MeshServiceServicer_to_server,
    PingRequest, PongResponse,
    AnnounceRequest, AnnounceResponse,
    FindPeerRequest, FindPeerResponse,
    GossipMessage, GossipAck,
    RequestVoteRequest, RequestVoteResponse,
    AppendEntriesRequest, AppendEntriesResponse,
    PBFTMessage, PBFTResponse,
    SyncRequest, SyncResponse,
    MeshEnvelope,
)

log = logging.getLogger("ciel.mesh.transport")


class MeshServicer(MeshServiceServicer):
    def __init__(self, node: GrpcTransport):
        self.node = node

    def Ping(self, request: PingRequest, context) -> PongResponse:
        peer_id = request.peer_id
        peer = self.node.discovery.get_peer(peer_id)
        if peer is None:
            peer = PeerInfo(peer_id=peer_id, state=1)
            self.node.discovery.add_peer(peer)
        else:
            peer.last_seen = time.time()
            peer.state = 1
        from . import proto
        known = [
            proto.Peer(peer_id=p.peer_id, address=p.address, port=p.port,
                       role=p.role, protocol_version=p.protocol_version,
                       public_key=p.public_key)
            for p in self.node.discovery.active_peers()[:20]
            if p.peer_id != peer_id
        ]
        return PongResponse(
            peer_id=self.node.identity.peer_id,
            timestamp=int(time.time() * 1000),
            nonce=request.nonce,
            known_peers=known,
        )

    def Announce(self, request: AnnounceRequest, context) -> AnnounceResponse:
        p = request.peer
        info = PeerInfo(
            peer_id=p.peer_id,
            address=p.address,
            port=p.port,
            role=p.role,
            state=2,
            public_key=p.public_key,
            protocol_version=p.protocol_version,
            capabilities=list(p.capabilities),
            last_seen=time.time(),
        )
        self.node.discovery.add_peer(info)
        return AnnounceResponse(
            accepted=True,
            peer_count=self.node.discovery.peer_count(),
        )

    def FindPeer(self, request: FindPeerRequest, context) -> FindPeerResponse:
        from . import proto
        peer = self.node.discovery.get_peer(request.target_id)
        if peer:
            return FindPeerResponse(
                found=True,
                peer=proto.Peer(
                    peer_id=peer.peer_id, address=peer.address,
                    port=peer.port, role=peer.role,
                    public_key=peer.public_key,
                ),
            )
        gossip_targets = self.node.discovery.active_peers()[:3]
        for target in gossip_targets:
            if target.peer_id != request.requester_id:
                try:
                    stub = self.node._get_stub(target)
                    if stub:
                        resp = stub.FindPeer(request, timeout=2)
                        if resp.found:
                            return resp
                except Exception:
                    continue
        return FindPeerResponse(found=False)

    def Gossip(self, request: GossipMessage, context) -> GossipAck:
        for cb in self.node._on_gossip:
            try:
                cb(request)
            except Exception:
                pass
        return GossipAck(accepted=True)

    def RequestVote(self, request: RequestVoteRequest, context) -> RequestVoteResponse:
        granted = self.node._handle_request_vote(request)
        return RequestVoteResponse(
            voter_id=self.node.identity.peer_id,
            term=request.term,
            vote_granted=granted,
        )

    def AppendEntries(self, request: AppendEntriesRequest, context) -> AppendEntriesResponse:
        success, last_index = self.node._handle_append_entries(request)
        return AppendEntriesResponse(
            follower_id=self.node.identity.peer_id,
            term=request.term,
            success=success,
            last_log_index=last_index,
        )

    def PBFTPrePrepare(self, request: PBFTMessage, context) -> PBFTResponse:
        return PBFTResponse(responder_id=self.node.identity.peer_id, accepted=True)

    def PBFTPrepare(self, request: PBFTMessage, context) -> PBFTResponse:
        return PBFTResponse(responder_id=self.node.identity.peer_id, accepted=True)

    def PBFTCommit(self, request: PBFTMessage, context) -> PBFTResponse:
        return PBFTResponse(responder_id=self.node.identity.peer_id, accepted=True)

    def SyncState(self, request: SyncRequest, context) -> SyncResponse:
        entries = self.node._get_sync_entries(
            request.last_sync_timestamp,
            list(request.interest_topics),
        )
        return SyncResponse(
            responder_id=self.node.identity.peer_id,
            entries=entries,
            sync_timestamp=int(time.time() * 1000),
            has_more=False,
        )

    def StreamMessages(self, request_iterator, context):
        for msg in request_iterator:
            self.node._gossip_queue.put(msg)
            yield msg


class GrpcTransport:
    def __init__(self, identity: NodeIdentity, discovery: PeerDiscovery,
                 host: str = "0.0.0.0", port: int = 0):
        self.identity = identity
        self.discovery = discovery
        self.host = host
        self.port = port
        self._server: grpc.Server | None = None
        self._stubs: dict[str, MeshServiceStub] = {}
        self._channels: dict[str, grpc.Channel] = {}
        self._gossip_queue: queue.Queue = queue.Queue()
        self._running = False
        self._raft_state = {"current_term": 0, "voted_for": None, "role": "follower"}
        self._raft_log: list[dict[str, Any]] = []
        self._sync_store: list[dict] = []
        self._on_gossip: list[Callable] = []
        self._on_peer_connected: list[Callable] = []

    def start(self) -> bool:
        self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        servicer = MeshServicer(self)
        add_MeshServiceServicer_to_server(servicer, self._server)
        port = self._server.add_insecure_port(f"{self.host}:{self.port or 0}")
        self.port = port
        self.identity.port = port
        self._server.start()
        self._running = True
        log.info("gRPC transport listening on %s:%d", self.host, self.port)
        return True

    def stop(self) -> None:
        self._running = False
        for ch in self._channels.values():
            try:
                ch.close()
            except Exception:
                pass
        self._channels.clear()
        self._stubs.clear()
        if self._server:
            self._server.stop(1)
            self._server = None

    def _get_stub(self, peer: PeerInfo) -> MeshServiceStub | None:
        if not peer.address or not peer.port:
            return None
        key = peer.peer_id
        if key in self._stubs:
            return self._stubs[key]
        addr = f"{peer.address}:{peer.port}"
        try:
            ch = grpc.insecure_channel(addr)
            stub = MeshServiceStub(ch)
            self._channels[key] = ch
            self._stubs[key] = stub
            return stub
        except Exception:
            return None

    def ping(self, peer: PeerInfo) -> float | None:
        stub = self._get_stub(peer)
        if not stub:
            return None
        start = time.time()
        try:
            resp = stub.Ping(PingRequest(
                peer_id=self.identity.peer_id,
                timestamp=int(time.time() * 1000),
                nonce=uuid.uuid4().hex[:8],
            ), timeout=5)
            elapsed = time.time() - start
            peer.latency = elapsed
            peer.last_seen = time.time()
            peer.state = 1
            for known in resp.known_peers:
                pid = known.peer_id
                if pid and pid != self.identity.peer_id and \
                   not self.discovery.get_peer(pid):
                    self.discovery.add_peer(PeerInfo(
                        peer_id=pid, address=known.address,
                        port=known.port, state=0,
                    ))
            return elapsed
        except Exception:
            return None

    def announce(self, peer: PeerInfo) -> bool:
        stub = self._get_stub(peer)
        if not stub:
            return False
        try:
            proto_peer = self.identity.to_peer_proto()
            resp = stub.Announce(AnnounceRequest(
                peer=proto_peer, ttl=3,
            ), timeout=5)
            return resp.accepted
        except Exception:
            return False

    def gossip(self, topic: str, payload: bytes,
               ttl: int = 3, target: str | None = None) -> None:
        msg = GossipMessage(
            sender_id=self.identity.peer_id,
            topic=topic,
            payload=payload,
            timestamp=int(time.time() * 1000),
            ttl=ttl,
            msg_id=uuid.uuid4().hex[:16],
        )
        peers = self.discovery.active_peers()
        if target:
            peers = [p for p in peers if p.peer_id == target]
        for peer in peers:
            if peer.peer_id == self.identity.peer_id:
                continue
            stub = self._get_stub(peer)
            if not stub:
                continue
            try:
                stub.Gossip(msg, timeout=3)
            except Exception:
                pass

    def request_vote(self, peer: PeerInfo) -> bool | None:
        stub = self._get_stub(peer)
        if not stub:
            return None
        try:
            resp = stub.RequestVote(RequestVoteRequest(
                candidate_id=self.identity.peer_id,
                term=self._raft_state["current_term"] + 1,
                last_log_index=len(self._raft_log),
                last_log_term=self._raft_log[-1]["term"] if self._raft_log else 0,
            ), timeout=5)
            return resp.vote_granted
        except Exception:
            return None

    def append_entries(self, peer: PeerInfo,
                       entries: list[dict]) -> bool | None:
        stub = self._get_stub(peer)
        if not stub:
            return None
        try:
            resp = stub.AppendEntries(AppendEntriesRequest(
                leader_id=self.identity.peer_id,
                term=self._raft_state["current_term"],
                prev_log_index=len(self._raft_log),
                prev_log_term=self._raft_log[-1]["term"] if self._raft_log else 0,
                leader_commit=0,
            ), timeout=5)
            return resp.success
        except Exception:
            return None

    def _handle_request_vote(self, request: RequestVoteRequest) -> bool:
        state = self._raft_state
        if request.term < state["current_term"]:
            return False
        if request.term == state["current_term"] and state["voted_for"] is not None:
            return False
        state["current_term"] = request.term
        state["voted_for"] = request.candidate_id
        state["role"] = "follower"
        return True

    def _handle_append_entries(self, request: AppendEntriesRequest) -> tuple[bool, int]:
        state = self._raft_state
        if request.term < state["current_term"]:
            return False, len(self._raft_log)
        state["current_term"] = request.term
        state["role"] = "follower"
        return True, len(self._raft_log)

    def _get_sync_entries(self, since: int, topics: list[str]) -> list[MeshEnvelope]:
        results = []
        for entry in self._sync_store:
            ts = entry.get("timestamp", 0)
            if ts > since:
                topic = entry.get("topic", "")
                if not topics or topic in topics:
                    results.append(MeshEnvelope(
                        msg_id=entry.get("msg_id", ""),
                        sender_id=entry.get("sender_id", ""),
                        msg_type=topic,
                        payload=json.dumps(entry.get("data", {})).encode(),
                        timestamp=ts,
                    ))
        return results

    def on_gossip(self, cb: Callable) -> None:
        self._on_gossip.append(cb)

    def on_peer_connected(self, cb: Callable) -> None:
        self._on_peer_connected.append(cb)
