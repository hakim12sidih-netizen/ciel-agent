/**
 * ═══════════════════════════════════════════════════════════════
 * LLM-TRANSMUTER — Self-improvement engine câblé à un vrai LLM
 * ═══════════════════════════════════════════════════════════════
 *
 * PHASE 3 du refactor Hydra :
 * 1. Lit le code source actuel d'un fichier
 * 2. Construit un prompt (intent + code + contraintes)
 * 3. Demande une proposition au LLM
 * 4. Fait valider par Aegis (audit statique)
 * 5. Crée la TransmutationProposal dans MetamorphicCore
 * 6. Applique (incubation + rollback auto si instable)
 *
 * Théorie :
 * - C'est le pattern "Generate-Validate-Apply" du formal methods
 * - Aegis joue le rôle d'un "trusted monitor" (cf. AI Safety literature)
 * - TransmutationBudget empêche l'auto-régression (rate limit)
 *
 * Le transmuter est un EventEmitter pour que d'autres modules
 * (TUI, monitoring) puissent réagir aux événements.
 */
import { EventEmitter } from 'events';
import * as fs from 'fs';
import * as path from 'path';
import logger from '../utils/logger.js';
import { TransmutationBudget } from './TransmutationBudget.js';
/**
 * Mappage des events émis :
 *  - 'transmutation.proposed'  : proposal créée (mais pas encore vérifiée)
 *  - 'transmutation.verified'  : Aegis a validé
 *  - 'transmutation.rejected'  : Aegis a refusé
 *  - 'transmutation.applied'   : code écrit sur disque
 *  - 'transmutation.rolledback': rollback effectué
 *  - 'transmutation.budget_denied': TransmutationBudget a bloqué
 *  - 'transmutation.complete'  : cycle complet (succès ou échec)
 */
export class LLMTransmuter extends EventEmitter {
    llm;
    aegis;
    metamorph;
    budget;
    options;
    transmutationCount = 0;
    constructor(llm, aegis, metamorph, budget = new TransmutationBudget(), options = {}) {
        super();
        this.llm = llm;
        this.aegis = aegis;
        this.metamorph = metamorph;
        this.budget = budget;
        this.options = {
            basePath: options.basePath ?? process.cwd(),
            currentDepth: options.currentDepth ?? 0,
            isMetamorphicCoreLocked: options.isMetamorphicCoreLocked ?? (() => false),
            incubationMs: options.incubationMs ?? 30_000,
        };
        // Override MetamorphicCore's incubation period if requested.
        // Useful in tests (incubationMs: 0) to skip the 30s default.
        this.metamorph.setIncubationPeriod(this.options.incubationMs);
        // Override MetamorphicCore's base path so resolveModulePath
        // targets the right directory (e.g. tests' tmpDir).
        this.metamorph.setBasePath(this.options.basePath);
        logger.info(`[LLM-Transmuter] 🦋 Initialized with LLM "${llm.name}", incubation: ${this.options.incubationMs}ms, base: ${this.options.basePath}`);
    }
    // ──────────────────────────────────────────────────────────
    // API PUBLIQUE
    // ──────────────────────────────────────────────────────────
    /**
     * Cycle complet de transmutation :
     * 1. Lit le fichier
     * 2. Construit le prompt
     * 3. Demande au LLM
     * 4. Vérifie via Aegis
     * 5. Crée + applique la proposal
     * 6. Incube + rollback si instable
     */
    async transmutate(filePath, intent) {
        const start = Date.now();
        const absPath = this.resolvePath(filePath);
        this.transmutationCount++;
        logger.info(`[LLM-Transmuter] 🦋 Transmutation #${this.transmutationCount}: ${filePath}`);
        logger.info(`[LLM-Transmuter]    Intent: ${intent}`);
        // 0. Budget check
        const budgetCheck = this.budget.check(absPath, {
            depth: this.options.currentDepth,
            lockCheck: this.options.isMetamorphicCoreLocked,
        });
        if (!budgetCheck.allowed) {
            logger.warn(`[LLM-Transmuter] 🚫 Budget denied: ${budgetCheck.reason} — ${budgetCheck.message}`);
            const result = {
                status: 'rejected_by_budget',
                filePath: absPath,
                reason: budgetCheck.message,
                budgetCheck,
                durationMs: Date.now() - start,
            };
            this.emit('transmutation.budget_denied', result);
            this.emit('transmutation.complete', result);
            return result;
        }
        // 1. Lire le code actuel
        let currentCode;
        try {
            currentCode = await this.readFile(absPath);
        }
        catch (err) {
            const result = {
                status: 'apply_failed',
                filePath: absPath,
                reason: `Cannot read file: ${err.message}`,
                durationMs: Date.now() - start,
            };
            this.emit('transmutation.complete', result);
            return result;
        }
        // 2. Build prompt + LLM call
        let proposedCode;
        try {
            const prompt = this.buildPrompt(currentCode, intent, filePath);
            proposedCode = await this.llm.complete(prompt, {
                maxTokens: 4096,
                temperature: 0.2, // Peu d'aléa pour la mut. de code
            });
        }
        catch (err) {
            const result = {
                status: 'llm_error',
                filePath: absPath,
                reason: `LLM call failed: ${err.message}`,
                durationMs: Date.now() - start,
            };
            this.emit('transmutation.complete', result);
            return result;
        }
        // 3. Aegis verification (audit statique)
        const aegisProof = await this.aegis.verifyCode(absPath, proposedCode);
        if (!aegisProof.isSafe) {
            logger.warn(`[LLM-Transmuter] 🛡️ Aegis rejected: ${aegisProof.errors.join('; ')}`);
            const result = {
                status: 'rejected_by_aegis',
                filePath: absPath,
                reason: aegisProof.errors.join('; '),
                aegisErrors: aegisProof.errors,
                patchSizeBytes: proposedCode.length,
                durationMs: Date.now() - start,
            };
            this.emit('transmutation.rejected', result);
            this.emit('transmutation.complete', result);
            return result;
        }
        logger.info(`[LLM-Transmuter] ✅ Aegis verified (score: ${aegisProof.score.toFixed(2)})`);
        // 4. Créer la proposal dans MetamorphicCore
        const gene = this.ensureModuleRegistered(absPath);
        const proposal = this.metamorph.proposeTransmutation(gene, intent, proposedCode, 0.5 // currentPhi fictif
        );
        this.emit('transmutation.proposed', { proposal, intent });
        // 5. Verify proposal (statut VERIFIED pour apply)
        const verified = await this.metamorph.verifyProposal(proposal.id);
        if (!verified) {
            const result = {
                status: 'rejected_by_aegis',
                filePath: absPath,
                proposalId: proposal.id,
                reason: 'MetamorphicCore.verifyProposal returned false',
                durationMs: Date.now() - start,
            };
            this.emit('transmutation.complete', result);
            return result;
        }
        this.emit('transmutation.verified', proposal);
        // 6. Apply
        const applied = await this.metamorph.applyTransmutation(proposal.id);
        if (!applied) {
            const result = {
                status: 'apply_failed',
                filePath: absPath,
                proposalId: proposal.id,
                reason: 'MetamorphicCore.applyTransmutation returned false',
                durationMs: Date.now() - start,
            };
            this.emit('transmutation.complete', result);
            return result;
        }
        this.budget.recordTransmutation(absPath);
        this.emit('transmutation.applied', { proposal, intent });
        // 7. Vérifier la stabilité post-application
        const result = {
            status: 'applied',
            filePath: absPath,
            proposalId: proposal.id,
            patchSizeBytes: proposedCode.length,
            budgetCheck,
            durationMs: Date.now() - start,
        };
        this.emit('transmutation.complete', result);
        return result;
    }
    /**
     * Variante "batch" : applique plusieurs transmutations en série.
     * S'arrête dès qu'une transmutation échoue (fail-fast).
     */
    async transmutateAll(intents) {
        const results = [];
        for (const { filePath, intent } of intents) {
            const result = await this.transmutate(filePath, intent);
            results.push(result);
            if (result.status !== 'applied') {
                logger.warn(`[LLM-Transmuter] ⏸️ Batch stopped at ${filePath}: ${result.status}`);
                break;
            }
        }
        return results;
    }
    // ──────────────────────────────────────────────────────────
    // PROMPT ENGINEERING
    // ──────────────────────────────────────────────────────────
    /**
     * Construit le prompt de transmutation.
     * Format : system prompt + user prompt avec code + intent.
     * Expose pour override dans les sous-classes.
     */
    buildPrompt(code, intent, filePath) {
        return `You are a code mutation engine. Your task is to propose a minimal, safe, incremental improvement to a TypeScript module.

INTENT: ${intent}

FILE: ${filePath}

CURRENT CODE:
\`\`\`typescript
${code}
\`\`\`

CONSTRAINTS (strict):
- Do not introduce any forbidden APIs: eval, exec, spawn, execSync, spawnSync.
- Do not introduce infinite loops without break conditions.
- Do not increase cyclomatic complexity by more than 5.
- Preserve all exported symbols (class names, function signatures, type names).
- Add tests for the new behavior if possible.
- Return ONLY the new code, no markdown fences, no commentary, no explanation.
- If the intent is unclear or the code cannot be safely improved, return "// NO_CHANGE" on the first line.`;
    }
    // ──────────────────────────────────────────────────────────
    // HELPERS
    // ──────────────────────────────────────────────────────────
    resolvePath(filePath) {
        if (path.isAbsolute(filePath))
            return filePath;
        return path.join(this.options.basePath, filePath);
    }
    async readFile(absPath) {
        if (!fs.existsSync(absPath)) {
            throw new Error(`File not found: ${absPath}`);
        }
        return fs.readFileSync(absPath, 'utf-8');
    }
    /**
     * Enregistre automatiquement le module dans MetamorphicCore
     * s'il ne l'est pas encore. Crée un gene "best-effort" basé
     * sur la complexité du code.
     */
    ensureModuleRegistered(absPath) {
        const moduleName = path.basename(absPath, '.ts');
        const arch = this.metamorph.getArchitecture();
        if (arch.has(moduleName)) {
            return arch.get(moduleName);
        }
        const code = fs.readFileSync(absPath, 'utf-8');
        const complexity = this.estimateComplexity(code);
        const gene = {
            id: `auto_${moduleName}_${Date.now()}`,
            moduleName,
            interfaces: [],
            dependencies: [],
            behavioralSignature: 'Auto-registered by LLMTransmuter',
            complexity,
            mutationRate: 0.5,
            generation: 0,
            lastTransmutation: 0,
            fitness: 0.5,
            isVital: false,
        };
        this.metamorph.registerModule(gene);
        return gene;
    }
    estimateComplexity(code) {
        const blocks = (code.match(/\{/g) || []).length;
        const branches = (code.match(/if|else|switch|for|while/g) || []).length;
        const calls = (code.match(/\.\w+\(/g) || []).length;
        return Math.round(blocks * 0.5 + branches * 1.5 + calls * 0.3);
    }
    // ──────────────────────────────────────────────────────────
    // OBSERVABILITÉ
    // ──────────────────────────────────────────────────────────
    getStats() {
        return {
            totalTransmutations: this.transmutationCount,
            budget: this.budget.getStats(),
        };
    }
}
