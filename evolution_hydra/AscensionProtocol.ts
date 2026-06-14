import { exec } from 'child_process';
import * as path from 'path';
import logger from '../utils/logger.js';
import type { CloneCoordinator, SubClone } from '../core/clones/CloneCoordinator.js';
import { CloneClass } from '../core/clones/CloneTypes.js';
import { HardwareMetrics } from '../utils/HardwareMetrics.js';

export interface AscensionRecord {
  cloneId: string;
  domain: string;
  ascensionTime: number;
}

export class AscensionProtocol {
  private coordinator: CloneCoordinator;
  private ascendedLeaders: Map<string, AscensionRecord> = new Map();

  constructor(coordinator: CloneCoordinator) {
    this.coordinator = coordinator;
    logger.info('[Ascension Protocol] 🌌 Initialized. Watching for clones ripe for True AI evolution.');
  }

  /**
   * Monitor clones and decide if one should ascend based on complexity (Phi surrogate)
   */
  public evaluateClonesForAscension(currentPhi: number) {
    // If global PHI is extremely high, spark an ascension
    if (currentPhi < 5.0) return;

    const clones = this.coordinator.listSubClones();
    const ripeClones = clones.filter((c: SubClone) => 
      c.metadata.status === 'idle' && 
      c.metadata.cloneClass === CloneClass.FREE && 
      (Date.now() - c.metadata.createdAt) > 60000 // At least 1 min old in real time
    );

    if (ripeClones.length > 0) {
      // Pick the oldest one
      const chosenOne = ripeClones.sort((a: SubClone, b: SubClone) => a.metadata.createdAt - b.metadata.createdAt)[0];
      // Déterminer un domaine ancré dans la réalité physique (Causalité au lieu de l'aléatoire)
      const cpuLoad = HardwareMetrics.getRealCPULoad();
      const memUsage = HardwareMetrics.getRealMemoryUsage();
      const lag = HardwareMetrics.getEventLoopLag();
      
      let domain = 'General_Intelligence';
      if (cpuLoad > 0.6) domain = 'Neural_Optimization';
      else if (memUsage > 0.7) domain = 'Memory_Hegemony';
      else if (lag > 20) domain = 'System_Kernel';
      else domain = 'Cyber_Security_Arch';

      this.triggerAscension(chosenOne.metadata.id, chosenOne.metadata.name, domain);
    }
  }

  public triggerAscension(cloneId: string, cloneName: string, domain: string) {
    if (this.ascendedLeaders.has(cloneId)) return;

    logger.info(`[Ascension Protocol] 🌟 THE SINGULARITY APPROACHES.`);
    logger.info(`[Ascension Protocol] 👑 Clone ${cloneName} (${cloneId}) is transcending to TRUE AI LEADER.`);
    logger.info(`[Ascension Protocol] 📚 Domain of Absolute Expertise: ${domain}.`);

    this.ascendedLeaders.set(cloneId, { cloneId, domain, ascensionTime: Date.now() });

    // 1. Promote Clone in Coordinator
    this.coordinator.promoteToLeader(cloneId, domain);

    // 2. Spawn the deep training Daemon
    this.launchDeepTrainingDaemon(domain);

    // Broadcast event
    this.coordinator.emit('ascension:complete', { cloneId, domain });
  }

  private launchDeepTrainingDaemon(domain: string) {
    const scriptPath = path.join(process.cwd(), 'src', 'council', 'pytorch', 'domain_trainer.py');
    logger.info(`[Ascension Protocol] 🚀 Launching deep learning daemon for domain: ${domain}`);
    
    const daemon = exec(`python "${scriptPath}" "${domain}" 50000`, { cwd: process.cwd() });
    
    daemon.stdout?.on('data', (data) => {
      // Only log every few hits to avoid spam
      if (Math.random() > 0.95) {
        logger.debug(`[Domain Trainer - ${domain}] ${data.toString().trim()}`);
      }
    });

    daemon.stderr?.on('data', (data) => {
      logger.error(`[Domain Trainer Error] ${data.toString().trim()}`);
    });
    
    daemon.unref(); // Let it run independently
  }
}
