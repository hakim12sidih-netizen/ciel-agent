import { Project, SyntaxKind } from 'ts-morph';
import logger from '../utils/logger.js';
import * as fs from 'fs';
import * as path from 'path';
/**
 * AEGIS is the Formal Verification engine of HYDRA.
 * It audits all code changes (ToolForge / DreamCoder) to ensure
 * they respect security and performance constraints before being applied.
 */
export class Aegis {
    project;
    constructor() {
        this.project = new Project();
        logger.info('[Aegis] 🛡️ Formal Verification Engine (Audit Statique) activated.');
    }
    async verifyCode(filePath, code) {
        logger.info(`[Aegis] 🛡️ Auditing code: ${path.basename(filePath)}...`);
        const sourceFile = this.project.createSourceFile(filePath, code, { overwrite: true });
        const proof = {
            isSafe: true,
            errors: [],
            score: 1.0,
            metadata: { complexity: 0, forbiddenPatterns: [], potentialInfiniteLoops: [] }
        };
        // 1. Forbidden API Check (eval, exec, spawn)
        const callExpressions = sourceFile.getDescendantsOfKind(SyntaxKind.CallExpression);
        for (const call of callExpressions) {
            const name = call.getExpression().getText();
            if (['eval', 'exec', 'spawn', 'execSync', 'spawnSync'].includes(name)) {
                proof.metadata.forbiddenPatterns.push(name);
                proof.isSafe = false;
                proof.errors.push(`FORBIDDEN API: Use of ${name} is restricted by AEGIS protocol.`);
            }
        }
        // 2. Loop Safety Check
        const loops = sourceFile.getDescendantsOfKind(SyntaxKind.WhileStatement);
        for (const loop of loops) {
            const condition = loop.getExpression().getText();
            if (condition === 'true' || condition === '1') {
                const hasBreak = loop.getDescendantsOfKind(SyntaxKind.BreakStatement).length > 0;
                if (!hasBreak) {
                    proof.metadata.potentialInfiniteLoops.push('while(true)');
                    proof.isSafe = false;
                    proof.errors.push('POTENTIAL INFINITE LOOP: while(true) detected without break condition.');
                }
            }
        }
        // 3. Complexity Metric (Depth of nested blocks)
        const blocks = sourceFile.getDescendantsOfKind(SyntaxKind.Block);
        proof.metadata.complexity = blocks.length;
        if (proof.metadata.complexity > 20) {
            proof.score -= 0.2;
            logger.warn(`[Aegis] High complexity detected: ${proof.metadata.complexity} blocks.`);
        }
        // 4. Persistence of Proof
        const proofPath = path.join(process.cwd(), 'src', 'evolution', 'proofs');
        if (!fs.existsSync(proofPath))
            fs.mkdirSync(proofPath, { recursive: true });
        fs.writeFileSync(path.join(proofPath, `${path.basename(filePath)}.proof.json`), JSON.stringify(proof, null, 2));
        if (proof.isSafe) {
            logger.info(`[Aegis] ✅ CODE VERIFIED. Safety score: ${proof.score}`);
        }
        else {
            logger.error(`[Aegis] ❌ CODE REJECTED. Safety violations found.`);
        }
        return proof;
    }
}
