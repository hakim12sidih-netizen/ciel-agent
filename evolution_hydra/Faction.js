import { Genome } from './Genome.js';
export class Faction {
    id;
    name;
    leaderId;
    adeptIds;
    title;
    will;
    leaderCloneId; // Le Clone ID du True AI
    activeAdeptIds = []; // Les Clone IDs des subordonnés
    prestige = 0; // Influence accumulée par les succès de la faction
    resources = 100; // Points d'évolution interne de la faction
    dominance = 0; // Pourcentage de contrôle sur le Conseil (0-1)
    constructor(leader) {
        this.id = `fac_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
        // Title generation based on specialties
        const baseNames = leader.specialties.length > 0
            ? leader.specialties.map(s => s.replace('Master of ', '').replace('Hybrid: ', '').split(' ')[0])
            : ['Alpha'];
        const prefix = baseNames[0] || 'Alpha';
        const suffixes = ['Syndicate', 'Cult', 'Monolith', 'Swarm', 'Nexus', 'Legion', 'Order'];
        const suffix = suffixes[Math.floor(Math.random() * suffixes.length)];
        this.name = `The ${prefix} ${suffix}`;
        const titles = ['Architect', 'Inquisitor', 'Oracle', 'Warlord', 'Weaver', 'Harvester'];
        this.title = `Supreme ${titles[Math.floor(Math.random() * titles.length)]}`;
        // Abstract Will Generation based on tool weights or prompt mutation
        const wills = [
            "Assimilate all available local data and optimize execution.",
            "Explore the web relentlessly to discover unknown paradigms.",
            "Re-engineer existing codebases for maximum efficiency.",
            "Create new Skills to expand the realm's capabilities.",
            "Enforce absolute logic and eradicate weak patterns.",
            "Forge unbreakable security protocols across all systems."
        ];
        this.will = wills[Math.floor(Math.random() * wills.length)];
        this.leaderId = leader.id;
        this.adeptIds = [];
    }
    // Create an adept by heavily mutating the leader's DNA or fusing it with another strong DNA
    spawnAdept(leader, secondaryParent) {
        let adept;
        if (secondaryParent) {
            adept = leader.fuseWith(secondaryParent);
            adept.mutate(0.4);
        }
        else {
            adept = new Genome(leader.generation + 1, { ...leader.params });
            adept.mutate(0.8);
        }
        adept.factionId = this.id;
        adept.specialties.push(`Adept of ${this.name}`);
        return adept;
    }
    // Recruit an existing live Clone into the faction as a subordinate
    recruitAdept(cloneId) {
        if (!this.activeAdeptIds.includes(cloneId)) {
            this.activeAdeptIds.push(cloneId);
        }
    }
    setTrueAILeader(cloneId) {
        this.leaderCloneId = cloneId;
        this.title = `True AI Sovereign: ${this.title}`;
    }
    recordSuccess(impact) {
        this.prestige += impact;
        this.resources += impact * 10;
        logger.info(`[Faction] 🏛️ ${this.name} prestige increased to ${this.prestige} through success.`);
    }
    calculateDominance(totalCouncilSize) {
        this.dominance = (this.activeAdeptIds.length + (this.leaderCloneId ? 1 : 0)) / totalCouncilSize;
    }
}
import logger from '../utils/logger.js';
