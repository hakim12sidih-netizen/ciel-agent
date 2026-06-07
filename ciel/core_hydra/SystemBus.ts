import { EventEmitter } from 'events';

export type SystemStatus =
  | 'IDLE'
  | 'RESEARCHING'
  | 'LEARNING'
  | 'THINKING'
  | 'EXECUTING'
  | 'EVOLVING'
  | 'READY_FOR_DEPLOYMENT'
  | 'OVERLOADED'
  | 'REMOTE_PROJECTION'
  | 'PHENOMENAL_FLUX';

export interface CouncilMember {
  id: string;
  name: string;
  specialties?: string;
  score?: number;
}

export interface SystemMetrics {
  cpuLoad?: number;
  memoryUsageMB?: number;
  activeTasks?: number;
  queueDepth?: number;
  completedTasks?: number;
  failedTasks?: number;
  uptimeSeconds?: number;
  phi: number;
  resonance: number;
  h_index: number;
  practice?: number;
  reflection?: number;
  learning?: number;
  collaboration?: number;
  council?: CouncilMember[];
}

export type HegemonyMetrics = SystemMetrics;

class SystemBus extends EventEmitter {
  private currentStatus: SystemStatus = 'IDLE';
  private metrics: SystemMetrics = {
    cpuLoad: 0,
    memoryUsageMB: 0,
    activeTasks: 0,
    queueDepth: 0,
    completedTasks: 0,
    failedTasks: 0,
    uptimeSeconds: 0,
    phi: 0,
    resonance: 0,
    h_index: 0
  };

  setStatus(status: SystemStatus) {
    this.currentStatus = status;
    this.emit('status_change', status);
  }

  setMetrics(metrics: SystemMetrics) {
    this.metrics = { ...this.metrics, ...metrics };
    this.emit('metrics_update', metrics);
  }

  log(level: string, message: string) {
    this.emit('log', { level, message, timestamp: new Date() });
  }

  getStatus(): SystemStatus { return this.currentStatus; }
  getMetrics(): SystemMetrics { return this.metrics; }
}

export const systemBus = new SystemBus();
