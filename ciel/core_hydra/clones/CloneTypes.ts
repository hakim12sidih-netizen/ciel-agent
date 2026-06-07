export enum CloneClass {
  PRECISE = 'precise',       // Fixed mission, limited tools, domain expert
  FREE = 'free',             // Open mission, all tools, autonomous
  TEMPORARY = 'temporary',   // One task, self-destructs
  PERMANENT = 'permanent',   // Background task, regular reports
  HIERARCHICAL = 'hierarchical', // Can create sub-clones
  SPIDER = 'spider',             // Remote compute harvester (eternal, OS-adaptive)
  AVATAR = 'avatar',             // Temporary projection onto external device
  PAVION = 'pavion',             // Remote USB/WiFi Drone acting as reverse-shell
  ORCHESTRATOR = 'orchestrator', // High-level agent that commands other agents
  TRUE_AI_LEADER = 'true_ai_leader'
}

export enum SovereignStatus {
  ACTIVE = 'active',
  DORMANT = 'dormant',
  CRITICAL = 'critical',  // Peut dépasser les quotas
  DEAD = 'dead'
}

export interface CloneMetadata {
  id: string;
  name: string;
  purpose: string;
  status: 'idle' | 'working' | 'paused' | 'done' | 'error';
  cloneClass: CloneClass;
  createdAt: number;
  lastReportAt?: number;
  agentConfigurationId?: string; // Configuration source
  specialties?: string;          // Agent specialties summary
  sovereignParent?: string;      // Le souverain dont dépend ce clone
  fitness?: number;              // Efficacité du clone
  genomeId?: string;
  dnaSummary?: string;
}
