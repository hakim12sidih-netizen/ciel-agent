"""
Transverse — SWARM : Fédération & Civilisation CIEL.

Protocole CIEL-NET v2.0 :
  - Couche 1 : Découverte & Identité (DHT + mDNS)
  - Couche 2 : Transport sécurisé (Noise XX + Double Ratchet)
  - Couche 3 : Consensus distribué (Raft + PBFT)
  - Couche 4 : Partage de connaissances (FedAvg, SCAFFOLD, Ditto)

5 rôles évolutifs :
  - REINE       : coordination, garde les skills N7
  - OUVRIÈRES   : production quotidienne
  - ÉCLAIREUSES : exploration de nouveaux domaines
  - GARDIENNES  : surveillance sécurité
  - MÈRES       : créent d'autres instances
"""
from __future__ import annotations

from ciel.swarm.core import (
    Role, PeerState, ConsensusType,
    Peer, Message, ConsensusEntry, ModelUpdate,
    Discovery, SecureTransport,
    RaftConsensus, PBFTConsensus, FederatedLearning,
    SwarmEngine,
)
__all__ = [
    "Role", "PeerState", "ConsensusType",
    "Peer", "Message", "ConsensusEntry", "ModelUpdate",
    "Discovery", "SecureTransport",
    "RaftConsensus", "PBFTConsensus", "FederatedLearning",
    "SwarmEngine",
]
