from __future__ import annotations

import time

import pytest
from ciel.swarm.core import (
    Role, PeerState, ConsensusType,
    Peer, Message, ConsensusEntry, ModelUpdate,
    Discovery, SecureTransport,
    RaftConsensus, PBFTConsensus, FederatedLearning,
    SwarmEngine,
)


class TestRole:
    def test_values(self):
        assert len(Role) == 5
        assert Role.REINE.value == "reine"
        assert Role.MERE.value == "mere"

    def test_all_roles(self):
        roles = {r.value for r in Role}
        assert roles == {"reine", "ouvriere", "eclaireuse", "gardienne", "mere"}


class TestPeerState:
    def test_order(self):
        assert PeerState.OFFLINE.value == 0
        assert PeerState.SYNCED.value == 3
        assert PeerState.FAULTY.value == 4


class TestPeer:
    def test_defaults(self):
        p = Peer(peer_id="p1")
        assert p.role == Role.OUVRIERE
        assert p.state == PeerState.OFFLINE
        assert p.trust_score == 0.5

    def test_custom(self):
        p = Peer("p2", "10.0.0.1", Role.REINE, PeerState.CONNECTED)
        assert p.address == "10.0.0.1"
        assert p.role == Role.REINE
        assert p.state == PeerState.CONNECTED


class TestMessage:
    def test_defaults(self):
        m = Message(sender="a", content="hello")
        assert m.msg_type == "data"
        assert m.ttl == 3
        assert m.signature == ""


class TestDiscovery:
    def test_add_peer(self):
        d = Discovery()
        p = d.add_peer("p1", "addr1", Role.ECLAIREUSE)
        assert p.peer_id == "p1"
        assert p.role == Role.ECLAIREUSE
        assert p.state == PeerState.DISCOVERED
        assert d.count() == 1

    def test_remove_peer(self):
        d = Discovery()
        d.add_peer("p1")
        assert d.remove_peer("p1") is True
        assert d.remove_peer("nonexistent") is False

    def test_get_peer(self):
        d = Discovery()
        d.add_peer("p1")
        assert d.get_peer("p1") is not None
        assert d.get_peer("nope") is None

    def test_all_peers(self):
        d = Discovery()
        d.add_peer("a")
        d.add_peer("b")
        assert len(d.all_peers()) == 2

    def test_peers_by_role(self):
        d = Discovery()
        d.add_peer("r1", role=Role.REINE)
        d.add_peer("o1", role=Role.OUVRIERE)
        d.add_peer("o2", role=Role.OUVRIERE)
        assert len(d.peers_by_role(Role.OUVRIERE)) == 2
        assert len(d.peers_by_role(Role.REINE)) == 1

    def test_register_seed(self):
        d = Discovery()
        d.register_seed("seed://1")
        d.register_seed("seed://2")
        assert len(d._seeds) == 2
        d.register_seed("seed://1")
        assert len(d._seeds) == 2

    def test_active_peers(self):
        d = Discovery()
        d.add_peer("p1", state=PeerState.CONNECTED)
        d.add_peer("p2", state=PeerState.OFFLINE)
        assert len(d.active_peers()) == 1


class TestSecureTransport:
    def test_create_session(self):
        t = SecureTransport()
        s = t.create_session("peer1", "pubkey123")
        assert s["peer_id"] == "peer1"
        assert s["public_key"] == "pubkey123"

    def test_encrypt_decrypt(self):
        t = SecureTransport()
        t.create_session("p1", "key")
        plaintext = "hello swarm"
        cipher = t.encrypt("p1", plaintext)
        assert cipher is not None
        decrypted = t.decrypt("p1", cipher)
        assert decrypted == plaintext

    def test_encrypt_unknown_peer(self):
        t = SecureTransport()
        assert t.encrypt("ghost", "data") is None

    def test_decrypt_unknown_peer(self):
        t = SecureTransport()
        assert t.decrypt("ghost", "aaaa") is None

    def test_session_count(self):
        t = SecureTransport()
        assert t.session_count() == 0
        t.create_session("a", "k1")
        t.create_session("b", "k2")
        assert t.session_count() == 2

    def test_message_count(self):
        t = SecureTransport()
        t.create_session("p", "k")
        t.encrypt("p", "msg1")
        t.encrypt("p", "msg2")
        assert t.message_count() == 2


class TestRaftConsensus:
    def test_initial_state(self):
        r = RaftConsensus("node1")
        assert r.role == "follower"
        assert r.term == 0
        assert r.voted_for is None

    def test_start_election(self):
        r = RaftConsensus("node1")
        term = r.start_election()
        assert term == 1
        assert r.role == "candidate"
        assert r.voted_for == "node1"

    def test_vote_for_granted(self):
        r = RaftConsensus("node1")
        assert r.vote_for("node2", 1) is True
        assert r.term == 1
        assert r.voted_for == "node2"

    def test_vote_for_stale_term(self):
        r = RaftConsensus("node1")
        r.term = 5
        assert r.vote_for("node2", 3) is False

    def test_vote_for_already_voted(self):
        r = RaftConsensus("node1")
        r.vote_for("node2", 1)
        assert r.vote_for("node3", 1) is False

    def test_receive_heartbeat(self):
        r = RaftConsensus("node1")
        r.term = 2
        assert r.receive_heartbeat("leader1", 2) is True
        assert r.leader_id == "leader1"
        assert r.role == "follower"

    def test_receive_heartbeat_stale(self):
        r = RaftConsensus("node1")
        r.term = 5
        assert r.receive_heartbeat("leader1", 3) is False

    def test_append_entry(self):
        r = RaftConsensus("node1")
        e = r.append_entry("store", {"key": "val"})
        assert e.index == 1
        assert e.command == "store"
        assert e.data["key"] == "val"

    def test_last_log(self):
        r = RaftConsensus("node1")
        assert r.last_log_index() == 0
        assert r.last_log_term() == 0
        r.append_entry("x")
        assert r.last_log_index() == 1

    def test_is_leader(self):
        r = RaftConsensus("n1")
        assert r.is_leader() is False
        r.role = "leader"
        assert r.is_leader() is True


class TestPBFTConsensus:
    def test_total_nodes(self):
        pbft = PBFTConsensus("n1", total_nodes=4)
        assert pbft.total_nodes == 4
        assert pbft.fault_tolerance() == 1

    def test_fault_tolerance(self):
        assert PBFTConsensus("n1", 4).fault_tolerance() == 1
        assert PBFTConsensus("n1", 7).fault_tolerance() == 2
        assert PBFTConsensus("n1", 1).fault_tolerance() == 0

    def test_pre_prepare(self):
        pbft = PBFTConsensus("n1")
        msg = pbft.pre_prepare({"op": "write", "data": "x"})
        assert msg["sequence"] == 1
        assert msg["sender"] == "n1"

    def test_prepare(self):
        pbft = PBFTConsensus("n1", total_nodes=4)
        msg = pbft.pre_prepare({"op": "write"})
        assert pbft.prepare(msg) is False
        for _ in range(3):
            pbft._prepared.append(msg)
        assert pbft.prepare(msg) is True


class TestFederatedLearning:
    def test_initial(self):
        fl = FederatedLearning()
        assert fl.get_round() == 0
        assert fl.get_history() == []

    def test_fed_avg_empty(self):
        fl = FederatedLearning()
        assert fl.fed_avg([]) == []

    def test_fed_avg_basic(self):
        fl = FederatedLearning()
        updates = [
            ModelUpdate("a", [1.0, 2.0], n_samples=10, accuracy=0.8),
            ModelUpdate("b", [3.0, 4.0], n_samples=20, accuracy=0.9),
        ]
        aggregated = fl.fed_avg(updates)
        assert len(aggregated) == 2
        assert fl.get_round() == 1
        assert len(fl.get_history()) == 1

    def test_scaffold(self):
        fl = FederatedLearning()
        result = fl.scaffold([0.5, 0.5], [0.7, 0.3], [0.1, 0.1], lr=0.1)
        assert len(result) == 2

    def test_ditto(self):
        fl = FederatedLearning()
        result = fl.ditto([0.5, 0.5], [0.8, 0.2], lam=0.5)
        assert len(result) == 2
        assert result[0] == pytest.approx(0.65)


class TestSwarmEngine:
    def test_create(self):
        e = SwarmEngine()
        assert e.peer_id.startswith("ciel-")
        assert e.role == Role.OUVRIERE

    def test_create_custom_id(self):
        e = SwarmEngine(peer_id="my-node")
        assert e.peer_id == "my-node"

    def test_set_role(self):
        e = SwarmEngine("n1")
        e.set_role(Role.REINE)
        assert e.role == Role.REINE
        assert e.discovery.get_peer("n1").role == Role.REINE

    def test_join(self):
        e = SwarmEngine("n1")
        peer = e.join()
        assert peer is not None
        assert e.discovery.count() == 1

    def test_send_message(self):
        e = SwarmEngine("n1")
        e2 = SwarmEngine("n2")
        e.join()
        e.discovery.add_peer("n2", "addr2", state=PeerState.CONNECTED)
        e2.discovery.add_peer("n1", "addr1", state=PeerState.CONNECTED)
        e2.transport.create_session("n1", "k1")
        msg = e.send_message("n2", "hello")
        assert msg is not None
        assert msg.sender == "n1"

    def test_send_message_offline(self):
        e = SwarmEngine("n1")
        e.join()
        msg = e.send_message("nonexistent", "hi")
        assert msg is None

    def test_raft_elect(self):
        e = SwarmEngine("n1")
        term = e.raft_elect()
        assert term >= 1
        assert e.raft.role == "candidate"

    def test_raft_append(self):
        e = SwarmEngine("n1")
        entry = e.raft_append("store", {"key": "value"})
        assert entry.index == 1
        assert entry.command == "store"

    def test_pbft_propose(self):
        e = SwarmEngine("n1")
        msg = e.pbft_propose({"op": "write"})
        assert "sequence" in msg
        assert msg["sender"] == "n1"

    def test_federated_round(self):
        e = SwarmEngine("n1")
        updates = [
            ModelUpdate("a", [1.0, 2.0], n_samples=10, accuracy=0.8),
            ModelUpdate("b", [3.0, 4.0], n_samples=20, accuracy=0.9),
        ]
        aggregated = e.federated_round(updates)
        assert len(aggregated) == 2

    def test_get_stats(self):
        e = SwarmEngine("n1")
        stats = e.get_stats()
        assert "peer_id" in stats
        assert "role" in stats
        assert "peers_discovered" in stats
        assert "messages_sent" in stats
        assert "raft_term" in stats
        assert "fed_round" in stats

    def test_process_join(self):
        e = SwarmEngine()
        r = e.process({"action": "join"})
        assert r["success"] is True
        assert "peer_id" in r

    def test_process_set_role(self):
        e = SwarmEngine("n1")
        r = e.process({"action": "set_role", "role": "reine"})
        assert r["success"] is True
        assert e.role == Role.REINE

    def test_process_set_role_bad(self):
        e = SwarmEngine("n1")
        r = e.process({"action": "set_role", "role": "fake"})
        assert r["success"] is False

    def test_process_discover(self):
        e = SwarmEngine("n1")
        e.join()
        r = e.process({"action": "discover"})
        assert r["success"] is True
        assert len(r["peers"]) == 1

    def test_process_raft_elect(self):
        e = SwarmEngine("n1")
        r = e.process({"action": "raft_elect"})
        assert r["success"] is True
        assert r["term"] >= 1

    def test_process_raft_append(self):
        e = SwarmEngine("n1")
        r = e.process({"action": "raft_append", "command": "set", "data": {"k": "v"}})
        assert r["success"] is True
        assert r["index"] == 1

    def test_process_pbft_propose(self):
        e = SwarmEngine("n1")
        r = e.process({"action": "pbft_propose", "request": {"op": "write"}})
        assert r["success"] is True
        assert r["sequence"] == 1

    def test_process_fed_round(self):
        e = SwarmEngine("n1")
        r = e.process({
            "action": "fed_round",
            "updates": [
                {"peer_id": "a", "weights": [1.0], "n_samples": 10, "accuracy": 0.8},
                {"peer_id": "b", "weights": [3.0], "n_samples": 20, "accuracy": 0.9},
            ],
        })
        assert r["success"] is True
        assert r["round"] == 1

    def test_process_stats(self):
        e = SwarmEngine("n1")
        r = e.process({"action": "stats"})
        assert r["success"] is True
        assert "stats" in r

    def test_process_bad_action(self):
        e = SwarmEngine("n1")
        r = e.process({"action": "bogus"})
        assert r["success"] is False

    def test_process_bad_input(self):
        e = SwarmEngine("n1")
        r = e.process("bad")
        assert r["success"] is False
