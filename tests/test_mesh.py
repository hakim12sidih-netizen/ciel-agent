from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import grpc
import pytest

from ciel.mesh.identity import NodeIdentity
from ciel.mesh.discovery import PeerDiscovery, PeerInfo
from ciel.mesh.node import MeshNode
from ciel.mesh.swarm_adapter import SwarmAdapter
from ciel.mesh.gateway_bridge import GatewayBridge
from ciel.mesh.transport import GrpcTransport, MeshServicer
from ciel.mesh.proto import (
    MeshServiceStub,
    PingRequest, PongResponse,
    AnnounceRequest, AnnounceResponse,
    FindPeerRequest, FindPeerResponse,
    GossipMessage, GossipAck,
    RequestVoteRequest, RequestVoteResponse,
    AppendEntriesRequest, AppendEntriesResponse,
    SyncRequest, SyncResponse,
    MeshEnvelope,
)


# ═══════════════════════════════════════════════════════════
# NodeIdentity
# ═══════════════════════════════════════════════════════════

class TestNodeIdentity:
    def test_generate(self):
        ident = NodeIdentity.generate()
        assert ident.peer_id.startswith("ciel-")
        assert len(ident.peer_id) > 5
        assert ident.protocol_version == 1

    def test_generate_custom_id(self):
        ident = NodeIdentity.generate(peer_id="test-node-42")
        assert ident.peer_id == "test-node-42"

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "identity.json"
            ident = NodeIdentity.generate(peer_id="save-test")
            ident.save(str(path))
            assert path.exists()
            loaded = NodeIdentity.load_or_generate(str(path))
            assert loaded.peer_id == "save-test"
            assert loaded.public_key.public_bytes_raw() == ident.public_key.public_bytes_raw()

    def test_load_or_generate_creates_new(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nonexistent.json"
            ident = NodeIdentity.load_or_generate(str(path))
            assert ident.peer_id.startswith("ciel-")
            assert path.exists()

    def test_sign_and_verify(self):
        ident = NodeIdentity.generate()
        data = b"hello mesh"
        sig = ident.sign(data)
        pub_bytes = ident.public_key.public_bytes_raw()
        assert ident.verify(data, sig, pub_bytes) is True
        # Wrong data should fail
        assert ident.verify(b"wrong data", sig, pub_bytes) is False
        # Wrong key should fail
        other = NodeIdentity.generate()
        other_pub = other.public_key.public_bytes_raw()
        assert ident.verify(data, sig, other_pub) is False

    def test_to_peer_proto(self):
        ident = NodeIdentity.generate(peer_id="proto-test")
        proto = ident.to_peer_proto()
        assert proto.peer_id == "proto-test"
        assert proto.protocol_version == 1

    def test_to_dict(self):
        ident = NodeIdentity.generate(peer_id="dict-test")
        d = ident.to_dict()
        assert d["peer_id"] == "dict-test"
        assert "created_at" in d


# ═══════════════════════════════════════════════════════════
# PeerDiscovery
# ═══════════════════════════════════════════════════════════

class TestPeerDiscovery:
    def test_add_peer(self):
        d = PeerDiscovery("self")
        info = PeerInfo(peer_id="peer-1", address="10.0.0.1", port=9001)
        d.add_peer(info)
        assert d.peer_count() == 1
        retrieved = d.get_peer("peer-1")
        assert retrieved is not None
        assert retrieved.address == "10.0.0.1"

    def test_add_peer_duplicate_updates(self):
        d = PeerDiscovery("self")
        d.add_peer(PeerInfo(peer_id="p1", trust_score=0.5))
        d.add_peer(PeerInfo(peer_id="p1", trust_score=0.9))
        assert d.peer_count() == 1
        assert d.get_peer("p1").trust_score == 0.9

    def test_remove_peer(self):
        d = PeerDiscovery("self")
        d.add_peer(PeerInfo(peer_id="p1"))
        d.add_peer(PeerInfo(peer_id="p2"))
        assert d.peer_count() == 2
        assert d.remove_peer("p1") is True
        assert d.peer_count() == 1
        assert d.remove_peer("nonexistent") is False

    def test_all_peers(self):
        d = PeerDiscovery("self")
        ids = ["a", "b", "c"]
        for pid in ids:
            d.add_peer(PeerInfo(peer_id=pid))
        assert len(d.all_peers()) == 3
        assert {p.peer_id for p in d.all_peers()} == set(ids)

    def test_active_peers(self):
        d = PeerDiscovery("self")
        d.add_peer(PeerInfo(peer_id="active1", state=2, last_seen=time.time()))
        d.add_peer(PeerInfo(peer_id="active2", state=1, last_seen=time.time()))
        d.add_peer(PeerInfo(peer_id="offline", state=0, last_seen=time.time()))
        active = d.active_peers()
        assert len(active) == 2
        assert all(p.state != 0 for p in active)

    def test_peers_by_role(self):
        d = PeerDiscovery("self")
        d.add_peer(PeerInfo(peer_id="leader", role="reine"))
        d.add_peer(PeerInfo(peer_id="worker1", role="ouvriere"))
        d.add_peer(PeerInfo(peer_id="worker2", role="ouvriere"))
        assert len(d.peers_by_role("ouvriere")) == 2
        assert len(d.peers_by_role("reine")) == 1
        assert len(d.peers_by_role("inexistant")) == 0

    def test_seeds(self):
        d = PeerDiscovery("self")
        d.register_seed("10.0.0.1:9000")
        d.register_seed("10.0.0.2:9000")
        assert len(d.seeds()) == 2
        d.register_seed("10.0.0.1:9000")  # duplicate
        assert len(d.seeds()) == 2

    def test_prune_stale(self):
        d = PeerDiscovery("self")
        d.add_peer(PeerInfo(peer_id="fresh", last_seen=time.time()))
        d.add_peer(PeerInfo(peer_id="stale", last_seen=time.time() - 1000))
        stale = d.prune_stale(timeout=500)
        assert "stale" in stale
        assert d.get_peer("stale") is None
        assert d.get_peer("fresh") is not None

    def test_event_callbacks(self):
        d = PeerDiscovery("self")
        added = []
        removed = []
        d.on_peer_added(lambda p: added.append(p.peer_id))
        d.on_peer_removed(lambda pid: removed.append(pid))
        d.add_peer(PeerInfo(peer_id="p1"))
        d.remove_peer("p1")
        assert "p1" in added
        assert "p1" in removed

    def test_to_dict(self):
        d = PeerDiscovery("self", namespace="test-net")
        d.add_peer(PeerInfo(peer_id="p1", state=2, last_seen=time.time()))
        d.register_seed("10.0.0.1:9000")
        info = d.to_dict()
        assert info["namespace"] == "test-net"
        assert info["peers"] == 1
        assert info["seeds"] == 1
        assert info["active"] == 1


# ═══════════════════════════════════════════════════════════
# GrpcTransport (in-process gRPC)
# ═══════════════════════════════════════════════════════════

class TestGrpcTransport:
    def _make_server_and_client(self):
        ident = NodeIdentity.generate(peer_id="server-node")
        disc = PeerDiscovery(ident.peer_id)
        transport = GrpcTransport(ident, disc, host="0.0.0.0", port=0)
        transport.start()
        # Create in-process channel to the server
        ch = grpc.insecure_channel(f"0.0.0.0:{transport.port}")
        stub = MeshServiceStub(ch)
        return transport, stub, ch

    def test_start_stop(self):
        ident = NodeIdentity.generate()
        disc = PeerDiscovery(ident.peer_id)
        t = GrpcTransport(ident, disc, port=0)
        assert t.start() is True
        assert t._running is True
        assert t.port > 0
        t.stop()
        assert t._running is False

    def test_ping(self):
        server, stub, ch = self._make_server_and_client()
        resp = stub.Ping(PingRequest(
            peer_id="test-client",
            timestamp=int(time.time() * 1000),
            nonce="abc123",
        ), timeout=5)
        assert resp.peer_id == "server-node"
        assert resp.nonce == "abc123"
        ch.close()
        server.stop()

    def test_ping_discovers_peer(self):
        server, stub, ch = self._make_server_and_client()
        stub.Ping(PingRequest(
            peer_id="new-peer", timestamp=0, nonce="x",
        ), timeout=5)
        peer = server.discovery.get_peer("new-peer")
        assert peer is not None
        assert peer.state == 1
        ch.close()
        server.stop()

    def test_announce(self):
        server, stub, ch = self._make_server_and_client()
        from ciel.mesh.proto import Peer as PeerProto
        resp = stub.Announce(AnnounceRequest(
            peer=PeerProto(peer_id="announcer", address="10.0.0.1", port=9001),
            ttl=3,
        ), timeout=5)
        assert resp.accepted is True
        peer = server.discovery.get_peer("announcer")
        assert peer is not None
        assert peer.address == "10.0.0.1"
        ch.close()
        server.stop()

    def test_find_peer_found(self):
        server, stub, ch = self._make_server_and_client()
        server.discovery.add_peer(PeerInfo(
            peer_id="target-peer", address="10.0.0.1", port=9001,
        ))
        resp = stub.FindPeer(FindPeerRequest(
            target_id="target-peer",
            requester_id="client",
        ), timeout=5)
        assert resp.found is True
        assert resp.peer.peer_id == "target-peer"
        ch.close()
        server.stop()

    def test_find_peer_not_found(self):
        server, stub, ch = self._make_server_and_client()
        resp = stub.FindPeer(FindPeerRequest(
            target_id="nonexistent",
            requester_id="client",
        ), timeout=5)
        assert resp.found is False
        ch.close()
        server.stop()

    def test_gossip(self):
        server, stub, ch = self._make_server_and_client()
        received = []
        server.on_gossip(lambda msg: received.append(msg))

        resp = stub.Gossip(GossipMessage(
            sender_id="gossiper",
            topic="test",
            payload=b"hello",
            msg_id="msg-1",
        ), timeout=5)
        assert resp.accepted is True
        assert len(received) == 1
        assert received[0].topic == "test"
        assert received[0].payload == b"hello"
        ch.close()
        server.stop()

    def test_request_vote_granted(self):
        server, stub, ch = self._make_server_and_client()
        resp = stub.RequestVote(RequestVoteRequest(
            candidate_id="candidate-1",
            term=5,
            last_log_index=0,
            last_log_term=0,
        ), timeout=5)
        assert resp.vote_granted is True
        assert resp.voter_id == "server-node"
        ch.close()
        server.stop()

    def test_request_vote_denied_lower_term(self):
        server, stub, ch = self._make_server_and_client()
        server._raft_state["current_term"] = 10
        resp = stub.RequestVote(RequestVoteRequest(
            candidate_id="candidate-1",
            term=5,
            last_log_index=0,
            last_log_term=0,
        ), timeout=5)
        assert resp.vote_granted is False
        ch.close()
        server.stop()

    def test_request_vote_denied_already_voted(self):
        server, stub, ch = self._make_server_and_client()
        server._raft_state["current_term"] = 1
        server._raft_state["voted_for"] = "other-candidate"
        resp = stub.RequestVote(RequestVoteRequest(
            candidate_id="candidate-1",
            term=1,
            last_log_index=0,
            last_log_term=0,
        ), timeout=5)
        # Same term but already voted for someone else
        assert server._raft_state["current_term"] == 1
        assert server._raft_state["voted_for"] == "other-candidate"
        ch.close()
        server.stop()

    def test_append_entries(self):
        server, stub, ch = self._make_server_and_client()
        server._raft_state["current_term"] = 3
        resp = stub.AppendEntries(AppendEntriesRequest(
            leader_id="leader-1",
            term=3,
            prev_log_index=0,
            prev_log_term=0,
            leader_commit=0,
        ), timeout=5)
        assert resp.success is True
        assert server._raft_state["role"] == "follower"
        ch.close()
        server.stop()

    def test_append_entries_stale_term(self):
        server, stub, ch = self._make_server_and_client()
        server._raft_state["current_term"] = 10
        resp = stub.AppendEntries(AppendEntriesRequest(
            leader_id="leader-1",
            term=5,
            prev_log_index=0,
            prev_log_term=0,
            leader_commit=0,
        ), timeout=5)
        assert resp.success is False
        ch.close()
        server.stop()

    def test_sync_state(self):
        server, stub, ch = self._make_server_and_client()
        server._sync_store.append({
            "msg_id": "m1", "sender_id": "s1", "topic": "test",
            "data": {"key": "val"}, "timestamp": 2000,
        })
        resp = stub.SyncState(SyncRequest(
            requester_id="client",
            last_sync_timestamp=1000,
            interest_topics=["test"],
        ), timeout=5)
        assert len(resp.entries) == 1
        assert resp.entries[0].msg_id == "m1"
        ch.close()
        server.stop()

    def test_on_gossip_callback(self):
        server, stub, ch = self._make_server_and_client()
        cb = MagicMock()
        server.on_gossip(cb)
        stub.Gossip(GossipMessage(sender_id="test", topic="t", payload=b"p"), timeout=5)
        assert cb.called
        ch.close()
        server.stop()

    def test_multiple_transports(self):
        """Two transport instances can be created independently."""
        i1 = NodeIdentity.generate(peer_id="node1")
        i2 = NodeIdentity.generate(peer_id="node2")
        d1 = PeerDiscovery(i1.peer_id)
        d2 = PeerDiscovery(i2.peer_id)
        t1 = GrpcTransport(i1, d1, port=0)
        t2 = GrpcTransport(i2, d2, port=0)
        t1.start()
        t2.start()
        assert t1.port > 0
        assert t2.port > 0
        assert t1.port != t2.port
        t1.stop()
        t2.stop()


# ═══════════════════════════════════════════════════════════
# MeshNode
# ═══════════════════════════════════════════════════════════

class TestMeshNode:
    def test_create_and_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = MeshNode(data_dir=tmp)
            ok = node.start()
            assert ok is True
            assert node._running is True
            stats = node.get_stats()
            assert stats["running"] is True
            assert stats["peers"] == 1  # self
            node.stop()
            assert node._running is False

    def test_identity_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = MeshNode(data_dir=tmp)
            node.start()
            node.save_state()
            identity_path = Path(tmp) / "identity.json"
            assert identity_path.exists()
            loaded = NodeIdentity.load_or_generate(str(identity_path))
            assert loaded.peer_id == node.identity.peer_id
            node.stop()

    def test_bootstrap_with_seeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = MeshNode(data_dir=tmp)
            node.start()
            # Register dummy seed (won't connect but registers it)
            node.join(["127.0.0.1:9999"])
            assert len(node.discovery.seeds()) == 1
            node.stop()

    def test_process_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = MeshNode(data_dir=tmp)
            node.start()

            # stats
            result = node.process({"action": "stats"})
            assert result["success"] is True

            # peers
            result = node.process({"action": "peers"})
            assert result["success"] is True
            assert len(result["peers"]) == 0  # only self

            # save
            result = node.process({"action": "save"})
            assert result["success"] is True

            # unknown action
            result = node.process({"action": "nonexistent"})
            assert result["success"] is False

            node.stop()

    def test_raft_election(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = MeshNode(data_dir=tmp)
            node.start()
            # Only one peer, should win election
            term = node.start_election()
            assert term is not None
            assert term >= 1
            stats = node.get_stats()
            assert stats["raft_role"] == "leader"
            node.stop()

    def test_append_log_as_leader(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = MeshNode(data_dir=tmp)
            node.start()
            node.start_election()
            entry = node.append_log("test-command", {"foo": "bar"})
            assert entry is not None
            assert entry["command"] == "test-command"
            assert entry["data"]["foo"] == "bar"
            assert entry["index"] == 1
            node.stop()

    def test_append_log_as_follower_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = MeshNode(data_dir=tmp)
            node.start()
            entry = node.append_log("cmd")
            assert entry is None  # not leader
            node.stop()

    def test_broadcast_gossip(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = MeshNode(data_dir=tmp)
            node.start()
            node.broadcast_gossip("test-topic", b"hello")
            stats = node.get_stats()
            assert stats["gossip_sent"] >= 1
            node.stop()

    def test_process_gossip_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = MeshNode(data_dir=tmp)
            node.start()
            result = node.process({
                "action": "gossip",
                "topic": "alert",
                "payload": {"severity": "high"},
            })
            assert result["success"] is True
            node.stop()

    def test_process_elect_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = MeshNode(data_dir=tmp)
            node.start()
            result = node.process({"action": "elect"})
            assert result["success"] is True
            assert result["term"] >= 1
            node.stop()

    def test_process_append_log_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            node = MeshNode(data_dir=tmp)
            node.start()
            node.start_election()
            result = node.process({
                "action": "append_log",
                "command": "deploy",
                "data": {"version": "2.0"},
            })
            assert result["success"] is True
            assert result["entry"]["command"] == "deploy"
            node.stop()

    def test_two_nodes_local_communication(self):
        i1 = NodeIdentity.generate(peer_id="alpha")
        i2 = NodeIdentity.generate(peer_id="beta")
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            n1 = MeshNode(identity=i1, host="127.0.0.1", port=0, data_dir=tmp1)
            n2 = MeshNode(identity=i2, host="127.0.0.1", port=0, data_dir=tmp2)
            n1.start()
            n2.start()

            # Connect n2 to n1
            ok = n2.connect_to("127.0.0.1", n1.port)
            assert ok is True
            time.sleep(0.5)

            # n2 should have discovered n1
            peers_n2 = n2.get_peers()
            assert any(p["peer_id"] == "alpha" for p in peers_n2)

            # n1 should have discovered n2 after ping
            peers_n1 = n1.get_peers()
            assert any(p["peer_id"] == "beta" for p in peers_n1)

            n1.stop()
            n2.stop()

    def test_gossip_between_nodes(self):
        i1 = NodeIdentity.generate(peer_id="gossip-a")
        i2 = NodeIdentity.generate(peer_id="gossip-b")
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            n1 = MeshNode(identity=i1, host="127.0.0.1", port=0, data_dir=tmp1)
            n2 = MeshNode(identity=i2, host="127.0.0.1", port=0, data_dir=tmp2)
            n1.start()
            n2.start()
            n2.connect_to("127.0.0.1", n1.port)
            time.sleep(0.5)

            n1.broadcast_gossip("hello", b"world")
            time.sleep(0.5)

            n1.stop()
            n2.stop()

    def test_raft_election_between_nodes(self):
        i1 = NodeIdentity.generate(peer_id="raft-a")
        i2 = NodeIdentity.generate(peer_id="raft-b")
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            n1 = MeshNode(identity=i1, host="127.0.0.1", port=0, data_dir=tmp1)
            n2 = MeshNode(identity=i2, host="127.0.0.1", port=0, data_dir=tmp2)
            n1.start()
            n2.start()
            n2.connect_to("127.0.0.1", n1.port)
            time.sleep(0.5)

            # Start election from n1
            term = n1.start_election()
            assert term is not None

            n1.stop()
            n2.stop()


# ═══════════════════════════════════════════════════════════
# SwarmAdapter
# ═══════════════════════════════════════════════════════════

class TestSwarmAdapter:
    def test_sync_peers_to_swarm(self):
        i1 = NodeIdentity.generate(peer_id="adapter-test")
        node = MeshNode(identity=i1)
        node.start()
        node.discovery.add_peer(PeerInfo(
            peer_id="remote-1", address="10.0.0.1", port=9001,
            role="reine", state=2,
        ))
        adapter = SwarmAdapter(node)
        adapter.sync_peers_to_swarm()
        sp = adapter.swarm.discovery.get_peer("remote-1")
        assert sp is not None
        assert sp.role.value == "reine"
        assert sp.state.value == 2
        node.stop()

    def test_process_sync(self):
        i1 = NodeIdentity.generate()
        node = MeshNode(identity=i1)
        node.start()
        adapter = SwarmAdapter(node)
        result = adapter.process({"action": "sync"})
        assert result["success"] is True
        node.stop()

    def test_process_join(self):
        i1 = NodeIdentity.generate()
        node = MeshNode(identity=i1)
        node.start()
        adapter = SwarmAdapter(node)
        result = adapter.process({"action": "join", "seeds": ["10.0.0.1:9000"]})
        assert result["success"] is True
        assert result["peer_id"] == i1.peer_id
        node.stop()

    def test_process_raft_elect(self):
        i1 = NodeIdentity.generate()
        node = MeshNode(identity=i1)
        node.start()
        adapter = SwarmAdapter(node)
        result = adapter.process({"action": "raft_elect"})
        assert result["success"] is True
        assert result["term"] >= 1
        node.stop()

    def test_process_raft_append(self):
        i1 = NodeIdentity.generate()
        node = MeshNode(identity=i1)
        node.start()
        adapter = SwarmAdapter(node)
        adapter.process({"action": "raft_elect"})
        result = adapter.process({"action": "raft_append", "command": "test"})
        assert result["success"] is True
        assert result["index"] >= 1
        node.stop()

    def test_send_message_to_known_peer(self):
        i1 = NodeIdentity.generate(peer_id="sender")
        node = MeshNode(identity=i1)
        node.start()
        node.discovery.add_peer(PeerInfo(
            peer_id="receiver", address="127.0.0.1", port=9999,
        ))
        adapter = SwarmAdapter(node)
        msg = adapter.send_message("receiver", "hello")
        assert msg is not None
        assert msg.content == "hello"
        node.stop()

    def test_send_message_to_unknown_peer(self):
        i1 = NodeIdentity.generate()
        node = MeshNode(identity=i1)
        node.start()
        adapter = SwarmAdapter(node)
        msg = adapter.send_message("unknown", "hello")
        assert msg is None
        node.stop()


# ═══════════════════════════════════════════════════════════
# GatewayBridge
# ═══════════════════════════════════════════════════════════

class TestGatewayBridge:
    def test_register_gateway_methods(self):
        ident = NodeIdentity.generate()
        node = MeshNode(identity=ident)
        node.start()
        bridge = GatewayBridge(node)
        gateway = MagicMock()
        bridge.register_gateway_methods(gateway)
        assert gateway.register_method.call_count >= 7
        node.stop()

    def test_cmd_status(self):
        ident = NodeIdentity.generate()
        node = MeshNode(identity=ident)
        node.start()
        bridge = GatewayBridge(node)
        result = bridge._cmd_status()
        assert result["status"] == "running"
        assert result["peer_id"] == ident.peer_id
        node.stop()

    def test_cmd_peers(self):
        ident = NodeIdentity.generate()
        node = MeshNode(identity=ident)
        node.start()
        bridge = GatewayBridge(node)
        result = bridge._cmd_peers()
        assert "peers" in result
        node.stop()

    def test_cmd_connect_missing_args(self):
        ident = NodeIdentity.generate()
        node = MeshNode(identity=ident)
        node.start()
        bridge = GatewayBridge(node)
        result = bridge._cmd_connect()
        assert result["status"] == "error"
        node.stop()

    def test_cmd_gossip(self):
        ident = NodeIdentity.generate()
        node = MeshNode(identity=ident)
        node.start()
        bridge = GatewayBridge(node)
        result = bridge._cmd_gossip(topic="test", payload={"key": "val"})
        assert result["status"] == "sent"
        node.stop()

    def test_cmd_find_missing_id(self):
        ident = NodeIdentity.generate()
        node = MeshNode(identity=ident)
        node.start()
        bridge = GatewayBridge(node)
        result = bridge._cmd_find()
        assert result["status"] == "error"
        node.stop()

    def test_cmd_elect(self):
        ident = NodeIdentity.generate()
        node = MeshNode(identity=ident)
        node.start()
        bridge = GatewayBridge(node)
        result = bridge._cmd_elect()
        assert result["status"] == "elected"
        node.stop()

    def test_cmd_stats(self):
        ident = NodeIdentity.generate()
        node = MeshNode(identity=ident)
        node.start()
        bridge = GatewayBridge(node)
        result = bridge._cmd_stats()
        assert result["status"] == "ok"
        assert "peer_id" in result["stats"]
        node.stop()


# ═══════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_identity_no_private_key_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "no_such_dir" / "identity.json"
            ident = NodeIdentity.load_or_generate(str(path))
            assert ident.peer_id is not None

    def test_discovery_empty(self):
        d = PeerDiscovery("self")
        assert d.all_peers() == []
        assert d.active_peers() == []
        assert d.peer_count() == 0
        assert d.get_peer("nonexistent") is None

    def test_discovery_prune_empty(self):
        d = PeerDiscovery("self")
        assert d.prune_stale() == []

    def test_transport_stop_without_start(self):
        ident = NodeIdentity.generate()
        disc = PeerDiscovery(ident.peer_id)
        t = GrpcTransport(ident, disc, port=0)
        t.stop()  # should not raise

    def test_node_stop_without_start(self):
        node = MeshNode()
        node.stop()  # should not raise

    def test_swarm_adapter_init_without_swarm(self):
        i1 = NodeIdentity.generate()
        node = MeshNode(identity=i1)
        node.start()
        adapter = SwarmAdapter(node)
        assert adapter.swarm is not None
        assert adapter.swarm.peer_id == i1.peer_id
        node.stop()

    def test_gossip_with_no_peers(self):
        node = MeshNode()
        node.start()
        node.broadcast_gossip("test", b"data")
        # Should not crash
        node.stop()

    def test_find_peer_nonexistent(self):
        node = MeshNode()
        node.start()
        found = node.find_peer("phantom-peer")
        assert found is None
        node.stop()

    def test_election_requires_multiple_peers_concept(self):
        node = MeshNode()
        node.start()
        term = node.start_election()
        assert term is not None  # single node always wins
        node.stop()

    def test_get_stats_before_start(self):
        node = MeshNode()
        stats = node.get_stats()
        assert stats["running"] is False

    def test_identity_default_values(self):
        ident = NodeIdentity.generate()
        assert ident.address == ""
        assert ident.port == 0
        assert ident.capabilities == []
