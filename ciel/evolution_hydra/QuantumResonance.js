import logger from '../utils/logger.js';
export class QuantumResonance {
    resolve(proposals) {
        logger.info(`[Quantum Resonance] Resolving ${proposals.length} proposal waves.`);
        const solutionGroups = {};
        for (const wave of proposals) {
            solutionGroups[wave.solutionId] ??= { totalAmplitude: 0, interference: 0, content: wave.content };
            const group = solutionGroups[wave.solutionId];
            let currentInterference = 0;
            for (const other of proposals) {
                if (other.cloneId === wave.cloneId)
                    continue;
                currentInterference += wave.amplitude * other.amplitude * Math.cos(wave.phase - other.phase);
            }
            group.totalAmplitude += wave.amplitude;
            group.interference += currentInterference;
        }
        let bestSolutionId = '';
        let maxCoherence = -Infinity;
        for (const [id, data] of Object.entries(solutionGroups)) {
            const coherence = data.totalAmplitude + data.interference;
            if (coherence > maxCoherence) {
                maxCoherence = coherence;
                bestSolutionId = id;
            }
        }
        const finalResult = solutionGroups[bestSolutionId];
        return {
            bestSolution: finalResult?.content ?? '',
            coherence: Number.isFinite(maxCoherence) ? maxCoherence : 0
        };
    }
}
