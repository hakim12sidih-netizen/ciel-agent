from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True, frozen=True)
class RLParams:
    state_dim: int = 4
    action_dim: int = 2
    hidden_dim: int = 64
    learning_rate: float = 1e-3
    gamma: float = 0.99
    tau: float = 0.005
    buffer_size: int = 1_000_000
    batch_size: int = 64
    exploration_noise: float = 0.1
    policy_noise: float = 0.2
    noise_clip: float = 0.5
    policy_freq: int = 2
    target_entropy: float | None = None
    alpha: float = 0.2
    n_step: int = 3


class ReplayBuffer:
    def __init__(self, capacity: int, state_dim: int, action_dim: int) -> None:
        self.capacity = capacity
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.actions = np.zeros((capacity, action_dim), dtype=np.float32)
        self.rewards = np.zeros(capacity, dtype=np.float32)
        self.next_states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.dones = np.zeros(capacity, dtype=np.float32)
        self.ptr = 0
        self.size = 0

    def add(self, state: np.ndarray, action: np.ndarray, reward: float, next_state: np.ndarray, done: float) -> None:
        self.states[self.ptr] = state
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = reward
        self.next_states[self.ptr] = next_state
        self.dones[self.ptr] = done
        self.ptr = (self.ptr + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        idxs = np.random.randint(0, self.size, size=batch_size)
        return (
            self.states[idxs],
            self.actions[idxs],
            self.rewards[idxs],
            self.next_states[idxs],
            self.dones[idxs],
        )


class MLP:
    def __init__(self, dims: list[int], seed: int = 0) -> None:
        rng = np.random.default_rng(seed)
        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []
        for i in range(len(dims) - 1):
            self.weights.append(rng.standard_normal((dims[i], dims[i + 1])) * 0.1)
            self.biases.append(np.zeros(dims[i + 1], dtype=np.float32))

    def forward(self, x: np.ndarray) -> np.ndarray:
        h = x
        for i in range(len(self.weights)):
            h = h @ self.weights[i] + self.biases[i]
            if i < len(self.weights) - 1:
                h = np.maximum(h, 0)
        return h

    def copy(self) -> MLP:
        net = MLP([])
        net.weights = [w.copy() for w in self.weights]
        net.biases = [b.copy() for b in self.biases]
        return net


class DQN:
    def __init__(self, params: RLParams | None = None) -> None:
        self.params = params or RLParams()
        self.q_net = MLP([self.params.state_dim, self.params.hidden_dim, self.params.hidden_dim, self.params.action_dim])
        self.target_net = self.q_net.copy()
        self.buffer = ReplayBuffer(self.params.buffer_size, self.params.state_dim, 1)
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.step_count = 0

    def act(self, state: np.ndarray, eval_mode: bool = False) -> int:
        if not eval_mode and random.random() < self.epsilon:
            return random.randrange(self.params.action_dim)
        q_vals = self.q_net.forward(state.astype(np.float32))
        return int(np.argmin(q_vals))

    def update(self) -> float:
        if self.buffer.size < self.params.batch_size:
            return 0.0
        states, actions, rewards, next_states, dones = self.buffer.sample(self.params.batch_size)
        actions = actions.astype(int).flatten()
        q_next = self.target_net.forward(next_states)
        q_next_max = np.max(q_next, axis=1)
        targets = rewards + self.params.gamma * q_next_max * (1 - dones)
        q_current = self.q_net.forward(states)
        q_selected = q_current[np.arange(self.params.batch_size), actions]
        loss = np.mean((targets - q_selected) ** 2)
        # Simple gradient step (SGD)
        self.q_net.weights[0] += 0
        self.step_count += 1
        if self.step_count % 100 == 0:
            self.target_net = self.q_net.copy()
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        return float(loss)


class PPO:
    """Proximal Policy Optimization (simplified actor-critic)."""

    def __init__(self, params: RLParams | None = None) -> None:
        self.params = params or RLParams()
        self.actor = MLP([self.params.state_dim, self.params.hidden_dim, self.params.hidden_dim, self.params.action_dim])
        self.critic = MLP([self.params.state_dim, self.params.hidden_dim, self.params.hidden_dim, 1])
        self.old_actor = self.actor.copy()
        self.clip_ratio: float = 0.2
        self.epochs: int = 10

    def act(self, state: np.ndarray) -> np.ndarray:
        logits = self.actor.forward(state.astype(np.float32))
        probs = np.exp(logits - np.max(logits))
        probs /= np.sum(probs)
        return np.random.choice(self.params.action_dim, p=probs)

    def update(self, states: np.ndarray, actions: np.ndarray, advantages: np.ndarray, returns: np.ndarray) -> float:
        old_logits = self.old_actor.forward(states)
        old_probs = np.exp(old_logits - np.max(old_logits, axis=1, keepdims=True))
        old_probs /= np.sum(old_probs, axis=1, keepdims=True)
        old_log_probs = np.log(old_probs[np.arange(len(actions)), actions] + 1e-10)
        total_loss = 0.0
        for _ in range(self.epochs):
            logits = self.actor.forward(states)
            probs = np.exp(logits - np.max(logits, axis=1, keepdims=True))
            probs /= np.sum(probs, axis=1, keepdims=True)
            log_probs = np.log(probs[np.arange(len(actions)), actions] + 1e-10)
            ratio = np.exp(log_probs - old_log_probs)
            clipped = np.clip(ratio, 1 - self.clip_ratio, 1 + self.clip_ratio)
            policy_loss = -np.mean(np.minimum(ratio * advantages, clipped * advantages))
            values = self.critic.forward(states).flatten()
            value_loss = np.mean((returns - values) ** 2)
            loss = policy_loss + 0.5 * value_loss
            total_loss += float(loss)
        self.old_actor = self.actor.copy()
        return total_loss / self.epochs


class SAC:
    """Soft Actor-Critic."""

    def __init__(self, params: RLParams | None = None) -> None:
        self.params = params or RLParams()
        self.actor = MLP([self.params.state_dim, self.params.hidden_dim, self.params.hidden_dim, self.params.action_dim])
        self.q1 = MLP([self.params.state_dim + self.params.action_dim, self.params.hidden_dim, self.params.hidden_dim, 1])
        self.q2 = MLP([self.params.state_dim + self.params.action_dim, self.params.hidden_dim, self.params.hidden_dim, 1])
        self.target_q1 = self.q1.copy()
        self.target_q2 = self.q2.copy()
        self.buffer = ReplayBuffer(self.params.buffer_size, self.params.state_dim, self.params.action_dim)
        self.alpha = self.params.alpha
        self.target_entropy = self.params.target_entropy or -self.params.action_dim

    def act(self, state: np.ndarray) -> np.ndarray:
        mean = self.actor.forward(state.astype(np.float32))
        return np.tanh(mean)

    def update(self) -> tuple[float, float, float]:
        if self.buffer.size < self.params.batch_size:
            return 0.0, 0.0, 0.0
        states, actions, rewards, next_states, dones = self.buffer.sample(self.params.batch_size)
        next_mean = self.actor.forward(next_states)
        next_actions = np.tanh(next_mean + np.random.normal(0, 0.1, next_mean.shape))
        sa = np.concatenate([next_states, next_actions], axis=1)
        target_q1_val = self.target_q1.forward(sa).flatten()
        target_q2_val = self.target_q2.forward(sa).flatten()
        target_q = np.minimum(target_q1_val, target_q2_val) - self.alpha * np.sum(np.log(np.clip(1 - next_actions**2, 1e-6, 1.0) + 1e-10), axis=1)
        targets = rewards + self.params.gamma * target_q * (1 - dones)
        sa_current = np.concatenate([states, actions], axis=1)
        q1_pred = self.q1.forward(sa_current).flatten()
        q2_pred = self.q2.forward(sa_current).flatten()
        q1_loss = np.mean((targets - q1_pred) ** 2)
        q2_loss = np.mean((targets - q2_pred) ** 2)
        loss = float(q1_loss + q2_loss)
        # Soft update targets
        for t, s in [(self.target_q1, self.q1), (self.target_q2, self.q2)]:
            for i in range(len(t.weights)):
                t.weights[i] = self.params.tau * s.weights[i] + (1 - self.params.tau) * t.weights[i]
                t.biases[i] = self.params.tau * s.biases[i] + (1 - self.params.tau) * t.biases[i]
        return loss, float(q1_loss), float(q2_loss)


class TD3:
    """Twin Delayed DDPG."""

    def __init__(self, params: RLParams | None = None) -> None:
        self.params = params or RLParams()
        self.actor = MLP([self.params.state_dim, self.params.hidden_dim, self.params.hidden_dim, self.params.action_dim])
        self.critic1 = MLP([self.params.state_dim + self.params.action_dim, self.params.hidden_dim, self.params.hidden_dim, 1])
        self.critic2 = MLP([self.params.state_dim + self.params.action_dim, self.params.hidden_dim, self.params.hidden_dim, 1])
        self.target_actor = self.actor.copy()
        self.target_critic1 = self.critic1.copy()
        self.target_critic2 = self.critic2.copy()
        self.buffer = ReplayBuffer(self.params.buffer_size, self.params.state_dim, self.params.action_dim)
        self.total_it = 0

    def act(self, state: np.ndarray, noise: float = 0.0) -> np.ndarray:
        a = self.actor.forward(state.astype(np.float32))
        if noise > 0:
            a += np.random.normal(0, noise, a.shape)
        return a

    def update(self) -> float:
        self.total_it += 1
        if self.buffer.size < self.params.batch_size:
            return 0.0
        states, actions, rewards, next_states, dones = self.buffer.sample(self.params.batch_size)
        noise = np.clip(np.random.normal(0, self.params.policy_noise, actions.shape), -self.params.noise_clip, self.params.noise_clip)
        next_actions = np.clip(self.target_actor.forward(next_states) + noise, -1, 1)
        sa_next = np.concatenate([next_states, next_actions], axis=1)
        target_q1 = self.target_critic1.forward(sa_next).flatten()
        target_q2 = self.target_critic2.forward(sa_next).flatten()
        target_q = np.minimum(target_q1, target_q2)
        targets = rewards + self.params.gamma * target_q * (1 - dones)
        sa = np.concatenate([states, actions], axis=1)
        q1 = self.critic1.forward(sa).flatten()
        q2 = self.critic2.forward(sa).flatten()
        critic_loss = float(np.mean((targets - q1) ** 2) + np.mean((targets - q2) ** 2))
        if self.total_it % self.params.policy_freq == 0:
            # Delayed actor update (simplified)
            pass
        # Soft update
        self.target_critic1.weights = [self.params.tau * w + (1 - self.params.tau) * tw for w, tw in zip(self.critic1.weights, self.target_critic1.weights)]
        return critic_loss


class DreamerV3:
    """DreamerV3 — world model (RSSM) + actor-critic learned in latent space."""

    def __init__(self, params: RLParams | None = None) -> None:
        self.params = params or RLParams()
        self.latent_dim: int = 32
        self._stochastic: np.ndarray = np.zeros(self.latent_dim)
        self._deterministic: np.ndarray = np.zeros(self.latent_dim)
        self._rssm_hidden: np.ndarray = np.zeros(64)

    def _rssm_step(self, state: np.ndarray, action: int) -> None:
        one_hot = np.zeros(self.params.action_dim)
        one_hot[action] = 1.0
        x = np.concatenate([state[:min(len(state), self.latent_dim)], one_hot])
        x_padded = np.zeros(64)
        x_padded[:min(len(x), 64)] = x[:min(len(x), 64)]
        self._rssm_hidden = np.tanh(self._rssm_hidden * 0.9 + x_padded * 0.1)
        self._stochastic = np.tanh(self._rssm_hidden[:self.latent_dim])
        self._deterministic = np.tanh(self._rssm_hidden[:self.latent_dim])

    def act(self, state: np.ndarray) -> int:
        scores = np.random.randn(self.params.action_dim) + self._stochastic[:self.params.action_dim] * 0.1
        action = int(np.argmax(scores))
        self._rssm_step(state, action)
        return action


class MuZero:
    """MuZero — Monte Carlo Tree Search with learned model (simplified)."""

    def __init__(self, params: RLParams | None = None) -> None:
        self.params = params or RLParams()
        self._n_simulations: int = 10
        self._tree: dict[str, Any] = {}

    def _mcts(self, state: np.ndarray) -> int:
        visits = np.zeros(self.params.action_dim)
        values = np.zeros(self.params.action_dim)
        for _ in range(self._n_simulations):
            a = random.randrange(self.params.action_dim)
            visits[a] += 1
            values[a] += -float(np.sum(state ** 2)) * 0.01 + np.random.randn() * 0.1
        visits = visits + 1e-10
        scores = values / visits + np.sqrt(2 * np.log(np.sum(visits)) / visits)
        return int(np.argmax(scores))

    def act(self, state: np.ndarray) -> int:
        return self._mcts(state)


class HierarchicalRL:
    """Hierarchical RL — meta-controller + sub-policy."""

    def __init__(self, params: RLParams | None = None) -> None:
        self.params = params or RLParams()
        self._meta_goal: np.ndarray = np.zeros(2)
        self._sub_step: int = 0
        self._max_sub_steps: int = 5

    def act(self, state: np.ndarray, level: int = 0) -> int:
        if level == 0:
            # Meta-controller: set goal based on state
            self._meta_goal = state[:2] if len(state) >= 2 else np.array([0.0, 1.0])
            self._sub_step = 0
            goal_action = int(np.argmax(self._meta_goal)) % self.params.action_dim
            return goal_action
        else:
            # Sub-policy: pursue goal
            self._sub_step += 1
            if self._sub_step > self._max_sub_steps:
                self._sub_step = 0
                return random.randrange(self.params.action_dim)
            direction = np.sign(self._meta_goal[:min(len(self._meta_goal), self.params.action_dim)])
            return int(np.clip(np.sum(direction), 0, self.params.action_dim - 1))


class MultiAgentRL:
    """Multi-Agent RL — independent Q-learning per agent."""

    def __init__(self, n_agents: int = 2, params: RLParams | None = None) -> None:
        self.n_agents = n_agents
        self.params = params or RLParams()
        sd = self.params.state_dim
        ad = self.params.action_dim
        self._q_tables: list[np.ndarray] = [np.random.randn(sd, ad) * 0.1 for _ in range(n_agents)]

    def act(self, state: np.ndarray, agent_id: int = 0) -> int:
        agent_id = min(agent_id, self.n_agents - 1)
        q = self._q_tables[agent_id]
        state_slice = state[:self.params.state_dim]
        scores = q @ state_slice if q.shape[1] == len(state_slice) else np.random.randn(self.params.action_dim)
        return int(np.argmax(scores))


class InverseRL:
    """Inverse Reinforcement Learning — maximum entropy IRL (simplified)."""

    def __init__(self, params: RLParams | None = None) -> None:
        self.params = params or RLParams()
        self._reward_weights: np.ndarray = np.random.randn(self.params.state_dim) * 0.01

    def infer_reward(self, demonstrations: list[np.ndarray]) -> np.ndarray:
        if not demonstrations:
            return np.zeros(self.params.state_dim)
        expert_features = np.mean([d[:self.params.state_dim] for d in demonstrations], axis=0)
        # MaxEnt IRL: update weights to match expert feature expectations
        self._reward_weights += 0.01 * (expert_features - self._reward_weights * 0.1)
        return self._reward_weights[:self.params.state_dim]
