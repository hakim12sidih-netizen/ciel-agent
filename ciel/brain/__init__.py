"""
Transverse — BRAIN : Cerveau Neurobiologique.

12 aires corticales (cf. Partie IV §4.2) :
  V1, V2, V4, IT, MT+, PF, PFC, ACC, HPC, AMY, BG, CB

Frameworks :
  - snnTorch + Norse + SpykeTorch (Phase 2)
  - sNeurones LIF + Izhikevich + AdEx
  - STDP + R-STDP + BCM
  - Surrogate Gradient + e-prop

Boucle thalamo-corticale : oscillations gamma/theta/delta
Cycle veille-sommeil artificiel précis
Réseaux de Hopfield modernes (Ramsauer 2020) : exp(N) capacité

Phase 0 : stubs alignés v∞.2. Implémentation Phase 2 (RAPHAËL).
"""
from __future__ import annotations
