import logger from '../../utils/logger.js';
import { AgentMemoryState } from './Pantheon.js';
import { PythonSkillExecutor } from '../../tools/execution/PythonSkillExecutor.js';
export var SkillLayer;
(function (SkillLayer) {
    SkillLayer[SkillLayer["COSMOS"] = 0] = "COSMOS";
    SkillLayer[SkillLayer["PERCEPTION"] = 1] = "PERCEPTION";
    SkillLayer[SkillLayer["COGNITION"] = 2] = "COGNITION";
    SkillLayer[SkillLayer["ACTION"] = 3] = "ACTION";
    SkillLayer[SkillLayer["METASYSTEM"] = 4] = "METASYSTEM";
})(SkillLayer || (SkillLayer = {}));
// ════════════════════════════════════════════════════════════
// CARTOGRAPHIE RÉELLE DES CAPACITÉS D'HYDRA → NŒUDS
// Chaque nœud = une VRAIE fonction exécutable du système
// ════════════════════════════════════════════════════════════
const SKILL_DEFINITIONS = {
    // ── PERCEPTION (1-60) : Capteurs & Entrées ──
    1: { name: 'file_read', tool: 'read_file' },
    2: { name: 'file_glob', tool: 'list_dir_glob' },
    3: { name: 'vision_capture', tool: 'observe_screen' },
    4: { name: 'vision_stream', tool: 'VisionStream' },
    5: { name: 'clipboard_read', tool: 'clipboard' },
    6: { name: 'web_fetch', tool: 'web_fetch' },
    7: { name: 'web_search', tool: 'web_search' },
    8: { name: 'crawler_swarm', tool: 'crawler_swarm' },
    9: { name: 'discord_listen', tool: 'DiscordBot' },
    10: { name: 'telegram_listen', tool: 'TelegramBot' },
    11: { name: 'whatsapp_listen', tool: 'WhatsAppBot' },
    12: { name: 'omnichannel_recv', tool: 'OmniChannelManager' },
    13: { name: 'system_audit', tool: 'local_device_action' },
    14: { name: 'computer_observe', tool: 'computer_control' },
    15: { name: 'memory_recall', tool: 'MemoryService' },
    16: { name: 'episodic_recall', tool: 'EpisodicVault' },
    17: { name: 'dream_recall', tool: 'DreamService' },
    18: { name: 'karmic_recall', tool: 'KarmicMemory' },
    19: { name: 'network_scan', tool: 'SpiderWeb.scan' },
    20: { name: 'spider_heartbeat', tool: 'SpiderWeb.heartbeat' },
    // ── Capacités Olympiennes : Perception ──
    21: { name: 'hydra_intent_parse', tool: 'HYDRA' },
    22: { name: 'hydra_emotion_detect', tool: 'HYDRA' },
    23: { name: 'hydra_language_id', tool: 'HYDRA' },
    24: { name: 'athena_context_scan', tool: 'ATHENA' },
    25: { name: 'athena_data_extract', tool: 'ATHENA' },
    26: { name: 'artemis_screen_read', tool: 'ARTEMIS' },
    27: { name: 'artemis_ocr', tool: 'ARTEMIS' },
    28: { name: 'artemis_pattern_match', tool: 'ARTEMIS' },
    29: { name: 'poseidon_proc_scan', tool: 'POSEIDON' },
    30: { name: 'poseidon_hw_detect', tool: 'POSEIDON' },
    31: { name: 'tethys_api_probe', tool: 'TETHYS' },
    32: { name: 'tethys_dns_resolve', tool: 'TETHYS' },
    33: { name: 'hades_memory_search', tool: 'HADES' },
    34: { name: 'hades_context_recall', tool: 'HADES' },
    35: { name: 'tartare_threat_scan', tool: 'TARTARE' },
    36: { name: 'tartare_vuln_detect', tool: 'TARTARE' },
    37: { name: 'psyche_mood_sense', tool: 'PSYCHE' },
    38: { name: 'psyche_tone_analyze', tool: 'PSYCHE' },
    39: { name: 'chronos_time_sense', tool: 'CHRONOS' },
    40: { name: 'chronos_deadline_scan', tool: 'CHRONOS' },
    ...Object.fromEntries([...Array(20)].map((_, i) => [i + 41, { name: `perception_reserve_${i + 1}`, tool: 'reserve' }])),
    // ── COGNITION (61-150) : Raisonnement & Analyse ──
    61: { name: 'deductive_reason', tool: 'QueryEngine.reason' },
    62: { name: 'abductive_reason', tool: 'QueryEngine.hypothesize' },
    63: { name: 'analogical_transfer', tool: 'QueryEngine.analogize' },
    64: { name: 'tree_planning', tool: 'QueryEngine.plan' },
    65: { name: 'conflict_resolve', tool: 'BCQ.arbitrate' },
    66: { name: 'omega_council', tool: 'omega_council_manager' },
    67: { name: 'alchemist_reason', tool: 'Alchemist' },
    68: { name: 'overseer_judge', tool: 'Overseer' },
    69: { name: 'omega_sync', tool: 'OmegaSync' },
    70: { name: 'synthesis_merge', tool: 'Synthesis' },
    71: { name: 'neural_forge_train', tool: 'neural_forge' },
    72: { name: 'sovereign_brain', tool: 'SovereignBrain' },
    73: { name: 'hegemony_strategy', tool: 'hegemony_strategist' },
    74: { name: 'skill_learn', tool: 'skill_memory' },
    75: { name: 'tool_forge', tool: 'forge_tool' },
    76: { name: 'tool_smith', tool: 'forge_tool' },
    77: { name: 'zeus_chronicle', tool: 'zeus_chronicle' },
    78: { name: 'gaia_knowledge', tool: 'Gaia' },
    79: { name: 'neural_forge_svc', tool: 'NeuralForge' },
    80: { name: 'genesis_crawl', tool: 'GenesisCrawl' },
    // ── Capacités Olympiennes : Cognition ──
    81: { name: 'zeus_arbitrate', tool: 'ZEUS' },
    82: { name: 'zeus_priority_rank', tool: 'ZEUS' },
    83: { name: 'zeus_delegate', tool: 'ZEUS' },
    84: { name: 'athena_rca', tool: 'ATHENA' },
    85: { name: 'athena_hypothesis', tool: 'ATHENA' },
    86: { name: 'athena_synthesis', tool: 'ATHENA' },
    87: { name: 'apollon_forecast', tool: 'APOLLON' },
    88: { name: 'apollon_risk_assess', tool: 'APOLLON' },
    89: { name: 'apollon_timeline', tool: 'APOLLON' },
    90: { name: 'hephaistos_arch', tool: 'HEPHAISTOS' },
    91: { name: 'hephaistos_debug', tool: 'HEPHAISTOS' },
    92: { name: 'hephaistos_refactor', tool: 'HEPHAISTOS' },
    93: { name: 'dionysos_brainstorm', tool: 'DIONYSOS' },
    94: { name: 'dionysos_aesthetic', tool: 'DIONYSOS' },
    95: { name: 'nemesis_bias_check', tool: 'NEMESIS' },
    96: { name: 'nemesis_fairness', tool: 'NEMESIS' },
    97: { name: 'nemesis_audit_agent', tool: 'NEMESIS' },
    98: { name: 'promethee_innovate', tool: 'PROMETHEE' },
    99: { name: 'promethee_breakthrough', tool: 'PROMETHEE' },
    100: { name: 'eris_contrarian', tool: 'ERIS' },
    101: { name: 'eris_stress_test', tool: 'ERIS' },
    102: { name: 'morphee_scenario_sim', tool: 'MORPHEE' },
    103: { name: 'morphee_what_if', tool: 'MORPHEE' },
    104: { name: 'hecate_reverse_eng', tool: 'HECATE' },
    105: { name: 'hecate_protocol_adapt', tool: 'HECATE' },
    106: { name: 'uranus_meaning', tool: 'URANUS' },
    107: { name: 'uranus_purpose', tool: 'URANUS' },
    108: { name: 'chronos_plan_long', tool: 'CHRONOS' },
    109: { name: 'chronos_retroaction', tool: 'CHRONOS' },
    110: { name: 'proteus_shape_decide', tool: 'PROTEUS' },
    ...Object.fromEntries([...Array(40)].map((_, i) => [i + 111, { name: `cognition_reserve_${i + 1}`, tool: 'reserve' }])),
    // ── ACTION (151-240) : Exécution & Modification ──
    151: { name: 'file_write', tool: 'write_to_file' },
    152: { name: 'file_edit', tool: 'edit_file' },
    153: { name: 'bash_execute', tool: 'run_command' },
    154: { name: 'python_execute', tool: 'python_lab' },
    155: { name: 'docker_run', tool: 'docker' },
    156: { name: 'blender_render', tool: 'blender_3d_render' },
    157: { name: 'universal_lab', tool: 'universal_lab' },
    158: { name: 'computer_control', tool: 'computer_control' },
    159: { name: 'clipboard_write', tool: 'clipboard' },
    160: { name: 'n8n_workflow', tool: 'n8n_manager' },
    161: { name: 'agent_spawn', tool: 'spawn_clone' },
    162: { name: 'avatar_project', tool: 'council_migration' },
    163: { name: 'dev_agent_code', tool: 'dev_agent' },
    164: { name: 'spider_deploy', tool: 'deploy_spider' },
    165: { name: 'pavion_launch', tool: 'pavion_control' },
    166: { name: 'discord_send', tool: 'DiscordBot' },
    167: { name: 'telegram_send', tool: 'TelegramBot' },
    168: { name: 'whatsapp_send', tool: 'WhatsAppBot' },
    169: { name: 'omnichannel_send', tool: 'OmniChannelManager' },
    170: { name: 'memory_store', tool: 'MemoryService' },
    171: { name: 'episodic_store', tool: 'EpisodicVault' },
    172: { name: 'tnvm_compress', tool: 'TitanNVM' },
    173: { name: 'clone_spawn', tool: 'LegionEngine' },
    174: { name: 'clone_kill', tool: 'LegionEngine' },
    175: { name: 'crispr_mutate', tool: 'CRISPR_Titan' },
    // ── Capacités Olympiennes : Action ──
    176: { name: 'hephaistos_code_gen', tool: 'HEPHAISTOS' },
    177: { name: 'hephaistos_test_write', tool: 'HEPHAISTOS' },
    178: { name: 'hephaistos_deploy', tool: 'HEPHAISTOS' },
    179: { name: 'dionysos_art_gen', tool: 'DIONYSOS' },
    180: { name: 'dionysos_music_gen', tool: 'DIONYSOS' },
    181: { name: 'dionysos_story_write', tool: 'DIONYSOS' },
    182: { name: 'poseidon_proc_kill', tool: 'POSEIDON' },
    183: { name: 'poseidon_service_ctl', tool: 'POSEIDON' },
    184: { name: 'poseidon_registry_edit', tool: 'POSEIDON' },
    185: { name: 'poseidon_install_pkg', tool: 'POSEIDON' },
    186: { name: 'tethys_http_call', tool: 'TETHYS' },
    187: { name: 'tethys_api_integrate', tool: 'TETHYS' },
    188: { name: 'tethys_cloud_sync', tool: 'TETHYS' },
    189: { name: 'hades_memory_write', tool: 'HADES' },
    190: { name: 'hades_context_save', tool: 'HADES' },
    191: { name: 'tartare_sandbox_run', tool: 'TARTARE' },
    192: { name: 'tartare_quarantine', tool: 'TARTARE' },
    193: { name: 'tartare_encrypt', tool: 'TARTARE' },
    194: { name: 'thanatos_purge', tool: 'THANATOS' },
    195: { name: 'thanatos_archive', tool: 'THANATOS' },
    196: { name: 'thanatos_compress', tool: 'THANATOS' },
    197: { name: 'psyche_adapt_tone', tool: 'PSYCHE' },
    198: { name: 'psyche_comfort', tool: 'PSYCHE' },
    199: { name: 'proteus_clone_morph', tool: 'PROTEUS' },
    200: { name: 'proteus_load_balance', tool: 'PROTEUS' },
    201: { name: 'hydra_format_output', tool: 'HydraNerveSystem' },
    202: { name: 'hydra_translate', tool: 'HydraNerveSystem' },
    203: { name: 'hydra_sarcasm', tool: 'HydraNerveSystem' },
    204: { name: 'hydra_luck', tool: 'HydraNerveSystem' },
    205: { name: 'hydra_stealth', tool: 'HydraNerveSystem' },
    206: { name: 'hydra_boundary', tool: 'HydraNerveSystem' },
    207: { name: 'hydra_erase_traces', tool: 'HydraNerveSystem' },
    208: { name: 'hydra_joke', tool: 'HydraNerveSystem' },
    209: { name: 'hydra_poetry', tool: 'HydraNerveSystem' },
    210: { name: 'hydra_barter', tool: 'HydraNerveSystem' },
    211: { name: 'hydra_neural_forge', tool: 'HydraNerveSystem' },
    212: { name: 'hydra_content_miner', tool: 'HydraNerveSystem' },
    213: { name: 'hydra_rlhf_opt', tool: 'HydraNerveSystem' },
    214: { name: 'hydra_harvest_social', tool: 'HydraNerveSystem' },
    215: { name: 'hydra_sanitize_data', tool: 'HydraNerveSystem' },
    216: { name: 'hydra_crispr_mutate', tool: 'HydraNerveSystem' },
    217: { name: 'hydra_genome_sync', tool: 'HydraNerveSystem' },
    218: { name: 'hydra_karma_update', tool: 'HydraNerveSystem' },
    ...Object.fromEntries([...Array(22)].map((_, i) => [i + 219, { name: `action_reserve_${i + 1}`, tool: 'reserve' }])),
    // ── METASYSTEM (241-300) : Auto-évolution ──
    241: { name: 'genome_read', tool: 'TitanGenome' },
    242: { name: 'genome_mutate', tool: 'CRISPR_Titan' },
    243: { name: 'genome_crossover', tool: 'TitanEcosystem' },
    244: { name: 'rl_learn', tool: 'TitanRL' },
    245: { name: 'rl_reward_12d', tool: 'TitanRL' },
    246: { name: 'meh_consolidate', tool: 'HierarchicalEpisodicMemory' },
    247: { name: 'arche_store', tool: 'ArcheDeNoe' },
    248: { name: 'arche_resurrect', tool: 'ArcheDeNoe' },
    249: { name: 'dream_weave', tool: 'DreamWeaver' },
    250: { name: 'phoenix_repair', tool: 'PhoenixProtocol' },
    251: { name: 'bcq_broadcast', tool: 'BCQ' },
    252: { name: 'legion_report', tool: 'LegionEngine' },
    253: { name: 'ecosystem_evolve', tool: 'TitanEcosystem' },
    254: { name: 'skill_forge_new', tool: 'forge_tool' },
    255: { name: 'hydra_orchestrate', tool: 'HydraCore' },
    // ── Capacités Olympiennes : Metasystem ──
    256: { name: 'zeus_meta_evaluate', tool: 'ZEUS' },
    257: { name: 'zeus_agent_promote', tool: 'ZEUS' },
    258: { name: 'nemesis_perf_audit', tool: 'NEMESIS' },
    259: { name: 'nemesis_punish', tool: 'NEMESIS' },
    260: { name: 'morphee_dream_train', tool: 'MORPHEE' },
    261: { name: 'morphee_nightmare_sim', tool: 'MORPHEE' },
    262: { name: 'eris_mutate_random', tool: 'ERIS' },
    263: { name: 'eris_escape_local_opt', tool: 'ERIS' },
    264: { name: 'promethee_meta_invent', tool: 'PROMETHEE' },
    265: { name: 'hecate_dark_integrate', tool: 'HECATE' },
    266: { name: 'uranus_destiny_guide', tool: 'URANUS' },
    267: { name: 'chronos_epoch_manage', tool: 'CHRONOS' },
    268: { name: 'proteus_shape_shift', tool: 'PROTEUS' },
    269: { name: 'thanatos_death_decide', tool: 'THANATOS' },
    ...Object.fromEntries([...Array(31)].map((_, i) => [i + 270, { name: `meta_reserve_${i + 1}`, tool: 'reserve' }])),
    // ── COSMOS (301-360) : Vision & Philosophie ──
    301: { name: 'teleology', tool: 'Uranus.purpose' },
    302: { name: 'cosmic_vision', tool: 'Uranus.vision' },
    303: { name: 'emergent_ethics', tool: 'Nemesis.judge' },
    304: { name: 'chaos_inject', tool: 'Eris.perturb' },
    305: { name: 'time_schedule', tool: 'Chronos.schedule' },
    306: { name: 'emotion_read', tool: 'Psyche.feel' },
    307: { name: 'dream_simulate', tool: 'Morphee.dream' },
    308: { name: 'archive_eternal', tool: 'Thanatos.archive' },
    309: { name: 'magic_interface', tool: 'Hecate.reverse' },
    310: { name: 'innovation_spark', tool: 'Promethee.ignite' },
    311: { name: 'uranus_cosmic_plan', tool: 'URANUS' },
    312: { name: 'uranus_myth_explain', tool: 'URANUS' },
    313: { name: 'nemesis_cosmic_balance', tool: 'NEMESIS' },
    314: { name: 'chronos_deep_time', tool: 'CHRONOS' },
    315: { name: 'psyche_collective_mood', tool: 'PSYCHE' },
    316: { name: 'morphee_multiverse', tool: 'MORPHEE' },
    317: { name: 'eris_entropy_calc', tool: 'ERIS' },
    318: { name: 'promethee_fire_steal', tool: 'PROMETHEE' },
    319: { name: 'hecate_crossroads', tool: 'HECATE' },
    320: { name: 'thanatos_legacy', tool: 'THANATOS' },
    ...Object.fromEntries([...Array(40)].map((_, i) => [i + 321, { name: `cosmos_reserve_${i + 1}`, tool: 'reserve' }])),
};
function getLayer(nodeId) {
    if (nodeId <= 60)
        return SkillLayer.PERCEPTION;
    if (nodeId <= 150)
        return SkillLayer.COGNITION;
    if (nodeId <= 240)
        return SkillLayer.ACTION;
    if (nodeId <= 300)
        return SkillLayer.METASYSTEM;
    return SkillLayer.COSMOS;
}
export class SkillGraph {
    nodes = new Map();
    constructor() {
        this.initialize();
    }
    initialize() {
        for (let id = 1; id <= 360; id++) {
            const def = SKILL_DEFINITIONS[id];
            this.nodes.set(id, {
                id,
                layer: getLayer(id),
                skill: def?.name ?? `node_${id}`,
                toolRef: def?.tool,
                connections: new Set(),
                state: AgentMemoryState.DORMANT,
                activationCount: 0,
                lastActivated: 0,
            });
        }
        // Wire connections: each node connects to 3 neighbors
        this.nodes.forEach((node) => {
            for (let offset = 1; offset <= 3; offset++) {
                const neighbor = node.id + offset;
                if (neighbor <= 360)
                    node.connections.add(neighbor);
            }
        });
        // Cross-layer connections (Perception → Action shortcuts)
        this.nodes.get(1)?.connections.add(151); // file_read → file_write
        this.nodes.get(7)?.connections.add(8); // web_search → crawler_swarm
        this.nodes.get(19)?.connections.add(164); // network_scan → spider_deploy
        this.nodes.get(61)?.connections.add(153); // reasoning → bash_execute
        this.nodes.get(66)?.connections.add(251); // omega_council → bcq_broadcast
    }
    /**
     * Load Python skills dynamically and inject them into the graph.
     */
    async loadPythonSkills() {
        const pythonSkills = await PythonSkillExecutor.listSkills();
        for (const skill of pythonSkills) {
            const newId = this.nodes.size + 1;
            let layer = SkillLayer.COGNITION;
            if (skill.layer === 'PERCEPTION')
                layer = SkillLayer.PERCEPTION;
            if (skill.layer === 'ACTION')
                layer = SkillLayer.ACTION;
            if (skill.layer === 'METASYSTEM')
                layer = SkillLayer.METASYSTEM;
            if (skill.layer === 'COSMOS')
                layer = SkillLayer.COSMOS;
            this.nodes.set(newId, {
                id: newId,
                layer,
                skill: `python_${skill.name}`,
                toolRef: 'PythonSkillExecutor', // Indique que c'est un skill Python
                connections: new Set([newId - 1, newId - 2]),
                state: AgentMemoryState.DORMANT,
                activationCount: 0,
                lastActivated: 0,
            });
            logger.info(`[SkillGraph] Injected Python skill: ${skill.name} (Node ${newId})`);
        }
    }
    /** Activate a set of nodes and record the timestamp */
    activateNodes(nodeIds) {
        const now = Date.now();
        for (const id of nodeIds) {
            const node = this.nodes.get(id);
            if (node) {
                node.state = AgentMemoryState.ACTIVE;
                node.activationCount++;
                node.lastActivated = now;
            }
        }
    }
    /** Deactivate nodes unused for more than 5 minutes */
    evictStaleNodes() {
        const threshold = Date.now() - 5 * 60 * 1000;
        this.nodes.forEach((node) => {
            if (node.state === AgentMemoryState.ACTIVE && node.lastActivated < threshold) {
                node.state = AgentMemoryState.DORMANT;
            }
        });
    }
    /** Resolve a skill name to its real tool reference */
    resolveToolRef(nodeId) {
        return this.nodes.get(nodeId)?.toolRef;
    }
    /** Find all nodes that reference a specific tool */
    findByTool(toolName) {
        const results = [];
        this.nodes.forEach(n => { if (n.toolRef === toolName)
            results.push(n); });
        return results;
    }
    selectNodes(complexity, tags) {
        const selected = [...Array(60)].map((_, i) => i + 1);
        if (complexity >= 4)
            selected.push(...[...Array(90)].map((_, i) => i + 61));
        if (complexity >= 8)
            selected.push(...[...Array(90)].map((_, i) => i + 151));
        if (tags.some(t => ['creative', 'chaos', 'simulation', 'innovation'].includes(t))) {
            selected.push(...[...Array(60)].map((_, i) => i + 241));
        }
        if (tags.some(t => ['cosmos', 'justice', 'emotion', 'time'].includes(t))) {
            selected.push(...[...Array(60)].map((_, i) => i + 301));
        }
        return selected;
    }
    getStats() {
        let active = 0;
        this.nodes.forEach((n) => { if (n.state === AgentMemoryState.ACTIVE)
            active++; });
        return { total: 360, active, dormant: 360 - active };
    }
    /** Add a new "anti-failure" node (Phoenix protocol) */
    addAntiFailureNode(skill) {
        const newId = this.nodes.size + 1;
        this.nodes.set(newId, {
            id: newId,
            layer: SkillLayer.METASYSTEM,
            skill,
            connections: new Set([1, 2, 3]),
            state: AgentMemoryState.HOT,
            activationCount: 0,
            lastActivated: Date.now(),
        });
        return newId;
    }
}
