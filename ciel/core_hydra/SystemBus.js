import { EventEmitter } from 'events';
class SystemBus extends EventEmitter {
    currentStatus = 'IDLE';
    metrics = {
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
    setStatus(status) {
        this.currentStatus = status;
        this.emit('status_change', status);
    }
    setMetrics(metrics) {
        this.metrics = { ...this.metrics, ...metrics };
        this.emit('metrics_update', metrics);
    }
    log(level, message) {
        this.emit('log', { level, message, timestamp: new Date() });
    }
    getStatus() { return this.currentStatus; }
    getMetrics() { return this.metrics; }
}
export const systemBus = new SystemBus();
