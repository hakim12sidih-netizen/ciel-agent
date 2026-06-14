/**
 * ReasoningEngine.ts
 *
 * 7 Types of Reasoning: Cognitive Workflow Phase 2
 * - Deductive (Logical Certainty)
 * - Inductive (General Rule from Observations)
 * - Abductive (Best Explanation - Sherlock Holmes)
 * - Causal (Pearl do-calculus)
 * - Counterfactual ("What if?")
 * - Analogical (Structure Mapping)
 * - Dialectical (Thesis/Antithesis/Synthesis)
 *
 * The math hot paths (Bayesian update, cosine similarity, confidence scoring,
 * entropy, KL, softmax) are delegated to a Rust kernel when available:
 *   `polyglot/rust/src/math.rs`
 * Pure TS fallback is used transparently if the binary isn't built.
 */

import {
  mathBayesian as rustBayesian,
  mathCosine as rustCosine,
  mathConfidence as rustConfidence,
  mathEntropy as rustEntropy,
  mathKL as rustKL,
  mathSoftmax as rustSoftmax,
} from '../polyglot/bridge.js';
import logger from '../utils/logger.js';

export interface Proposition {
  statement: string;
  confidence: number; // 0-1
  source?: string;
}

export interface ReasoningResult {
  type: string;
  conclusion: string;
  reasoning: string;
  confidence: number;
  premises: Proposition[];
  metadata?: Record<string, any>;
}

export interface CausalModel {
  variables: { [key: string]: string };
  relationships: Array<{ from: string; to: string; strength: number }>;
  interventions?: { [key: string]: unknown };
}

/**
 * MathKernel — delegates numerical hot paths to Rust (`polyglot/rust/src/math.rs`).
 * Falls back to TypeScript on subprocess failure.
 */
export class MathKernel {
  /** Cosine similarity between two vectors in [0, 1] range (or [-1, 1] if signed). */
  public static async cosine(a: number[], b: number[]): Promise<number> {
    try {
      return await rustCosine(a, b);
    } catch {
      return MathKernel.cosinePure(a, b);
    }
  }

  /** Pure-TS cosine (no subprocess, used as fallback and in benchmarks). */
  public static cosinePure(a: number[], b: number[]): number {
    if (a.length !== b.length || a.length === 0) return 0;
    let dot = 0, na = 0, nb = 0;
    for (let i = 0; i < a.length; i++) {
      dot += a[i]! * b[i]!;
      na += a[i]! * a[i]!;
      nb += b[i]! * b[i]!;
    }
    na = Math.sqrt(na);
    nb = Math.sqrt(nb);
    if (na === 0 || nb === 0) return 0;
    return dot / (na * nb);
  }

  /** Bayesian posterior P(H|E) = LR * P(H) / (LR * P(H) + 1 - P(H)). */
  public static async bayesian(prior: number, likelihoodRatio: number): Promise<number> {
    try {
      return await rustBayesian(prior, likelihoodRatio);
    } catch {
      return MathKernel.bayesianPure(prior, likelihoodRatio);
    }
  }

  /** Pure-TS Bayesian. */
  public static bayesianPure(prior: number, likelihoodRatio: number): number {
    const denom = likelihoodRatio * prior + (1 - prior);
    return denom === 0 ? 0 : (likelihoodRatio * prior) / denom;
  }

  /** Inductive confidence: min(0.95, 0.5 + ratio * 0.45). */
  public static async confidence(supportCount: number, totalCount: number): Promise<number> {
    try {
      return await rustConfidence(supportCount, totalCount);
    } catch {
      if (totalCount === 0) return 0;
      const ratio = supportCount / totalCount;
      return Math.min(0.95, 0.5 + ratio * 0.45);
    }
  }

  /** Shannon entropy in nats. */
  public static async entropy(p: number[]): Promise<number> {
    try {
      return await rustEntropy(p);
    } catch {
      let h = 0;
      for (const pi of p) {
        if (pi > 0) h -= pi * Math.log(pi);
      }
      return h;
    }
  }

  /** KL divergence D(P || Q) in nats. Returns +Infinity if Q has zero where P>0. */
  public static async kl(p: number[], q: number[]): Promise<number> {
    try {
      return await rustKL(p, q);
    } catch {
      if (p.length !== q.length) return 0;
      let d = 0;
      for (let i = 0; i < p.length; i++) {
        if (p[i]! > 0) {
          if (q[i]! <= 0) return Infinity;
          d += p[i]! * Math.log(p[i]! / q[i]!);
        }
      }
      return d;
    }
  }

  /** Numerically stable softmax. */
  public static async softmax(x: number[]): Promise<number[]> {
    try {
      return await rustSoftmax(x);
    } catch {
      return MathKernel.softmaxPure(x);
    }
  }

  /** Pure-TS softmax. */
  public static softmaxPure(x: number[]): number[] {
    if (x.length === 0) return [];
    const m = Math.max(...x);
    const exps = x.map(v => Math.exp(v - m));
    const sum = exps.reduce((a, b) => a + b, 0);
    return exps.map(v => v / sum);
  }
}

// ============================================================================
// DEDUCTIVE REASONING: Logical Certainty (Modus Ponens)
// ============================================================================

export class DeductiveReasoner {
  /**
   * Modus Ponens: If P then Q. P is true. Therefore Q is true.
   */
  reason(premise1: string, premise2: string, rule: string): ReasoningResult {
    // Parse: "If [condition] then [conclusion]"
    const ruleMatch = rule.match(/if\s+(.+?)\s+then\s+(.+)/i);
    
    return {
      type: 'DEDUCTIVE',
      conclusion: ruleMatch ? ruleMatch[2] : '',
      reasoning: `
Given:
  - Major premise: ${rule}
  - Minor premise: ${premise2}
Logical form: Modus Ponens
  - If ${ruleMatch?.[1]} → ${ruleMatch?.[2]}
  - ${premise2}
  - Therefore: ${ruleMatch?.[2]} ∎
Certainty: Deductive logic guarantees conclusion if premises are true.
      `,
      confidence: premise1 && premise2 ? 0.99 : 0.5,
      premises: [
        { statement: rule, confidence: 0.95 },
        { statement: premise2, confidence: 0.90 }
      ]
    };
  }

  /**
   * Modus Tollens: If P then Q. Q is false. Therefore P is false.
   */
  reasonNegation(premise: string, negatedConclusion: string, rule: string): ReasoningResult {
    return {
      type: 'DEDUCTIVE_NEGATION',
      conclusion: `NOT ${premise}`,
      reasoning: `
Modus Tollens:
  - If ${premise} → Q
  - Q is false: ${negatedConclusion}
  - Therefore: NOT ${premise}
Certainty: Logically valid.
      `,
      confidence: 0.98,
      premises: [
        { statement: rule, confidence: 0.95 },
        { statement: negatedConclusion, confidence: 0.90 }
      ]
    };
  }
}

// ============================================================================
// INDUCTIVE REASONING: General Rule from Observations
// ============================================================================

export class InductiveReasoner {
  /**
   * Generalization from observed instances.
   * Strength depends on sample size and representativeness.
   * Confidence is computed by MathKernel (Rust if available, TS fallback).
   */
  async reason(observations: Proposition[], target: string): Promise<ReasoningResult> {
    const supportCount = observations.filter(o => o.confidence > 0.7).length;
    const confidence = await MathKernel.confidence(supportCount, observations.length);
    const supportRatio = observations.length === 0 ? 0 : supportCount / observations.length;

    return {
      type: 'INDUCTIVE',
      conclusion: target,
      reasoning: `
Inductive Generalization:
  - Observed instances: ${observations.length}
  - Supporting evidence: ${supportCount} (${(supportRatio * 100).toFixed(1)}%)
  - Pattern: ${target}
  - Confidence: ${(confidence * 100).toFixed(1)}%
Note: Induction is probabilistic. More evidence → higher confidence.
Weakness: Sample bias, hasty generalization possible.
      `,
      confidence,
      premises: observations
    };
  }

  /**
   * Bayesian induction: Update belief based on new evidence.
   * Math is delegated to Rust (f64 precision, no overflow guards needed).
   */
  async bayesianUpdateAsync(
    priorProbability: number,
    likelihoodRatio: number, // P(E|H) / P(E|¬H)
    evidence: string
  ): Promise<ReasoningResult> {
    let posterior: number;
    try {
      posterior = await rustBayesian(priorProbability, likelihoodRatio);
    } catch (e) {
      // TS fallback
      const denom = likelihoodRatio * priorProbability + (1 - priorProbability);
      posterior = denom === 0 ? 0 : (likelihoodRatio * priorProbability) / denom;
      logger.debug(`[InductiveReasoner] Rust math unavailable, TS fallback: ${e instanceof Error ? e.message : e}`);
    }
    return {
      type: 'INDUCTIVE_BAYESIAN',
      conclusion: `Updated probability: ${(posterior * 100).toFixed(2)}%`,
      reasoning: `
Bayesian Update:
  - Prior probability: ${(priorProbability * 100).toFixed(2)}%
  - Evidence: ${evidence}
  - Likelihood ratio (P(E|H)/P(E|¬H)): ${likelihoodRatio.toFixed(2)}
  - Posterior: ${(posterior * 100).toFixed(2)}%
Critical insight: Most people ignore base rates. This corrects that.
      `,
      confidence: 0.95,
      premises: [
        { statement: `Prior: ${(priorProbability * 100).toFixed(2)}%`, confidence: 0.9 },
        { statement: evidence, confidence: 0.85 }
      ]
    };
  }

  /**
   * Sync wrapper kept for backward compatibility.
   */
  bayesianUpdate(
    priorProbability: number,
    likelihoodRatio: number,
    evidence: string
  ): ReasoningResult {
    // Compute synchronously in TS, mirror of rustBayesian
    const denom = likelihoodRatio * priorProbability + (1 - priorProbability);
    const posterior = denom === 0 ? 0 : (likelihoodRatio * priorProbability) / denom;
    return {
      type: 'INDUCTIVE_BAYESIAN',
      conclusion: `Updated probability: ${(posterior * 100).toFixed(2)}%`,
      reasoning: `
Bayesian Update:
  - Prior probability: ${(priorProbability * 100).toFixed(2)}%
  - Evidence: ${evidence}
  - Likelihood ratio (P(E|H)/P(E|¬H)): ${likelihoodRatio.toFixed(2)}
  - Posterior: ${(posterior * 100).toFixed(2)}%
Critical insight: Most people ignore base rates. This corrects that.
      `,
      confidence: 0.95,
      premises: [
        { statement: `Prior: ${(priorProbability * 100).toFixed(2)}%`, confidence: 0.9 },
        { statement: evidence, confidence: 0.85 }
      ]
    };
  }
}

// ============================================================================
// ABDUCTIVE REASONING: Best Explanation (Sherlock Holmes)
// ============================================================================

export class AbductiveReasoner {
  /**
   * Inference to the Best Explanation.
   * Given observations, find the most likely explanation.
   */
  reason(observation: string, hypotheses: Array<{ explanation: string; likelihood: number }>): ReasoningResult {
    const sorted = [...hypotheses].sort((a, b) => b.likelihood - a.likelihood);
    const bestHypothesis = sorted[0];

    return {
      type: 'ABDUCTIVE',
      conclusion: bestHypothesis.explanation,
      reasoning: `
Inference to Best Explanation:
  - Observation: ${observation}
  - Candidate explanations:
${hypotheses.map((h, i) => `    ${i + 1}. "${h.explanation}" (likelihood: ${(h.likelihood * 100).toFixed(1)}%)`).join('\n')}
  - Best explanation: "${bestHypothesis.explanation}"
  - Why: Highest likelihood, simplest, most coherent with known facts

This is how detectives work. Not proof, but best guess given evidence.
Rigor: Should be falsifiable; alternative explanations considered.
      `,
      confidence: Math.min(bestHypothesis.likelihood, 0.85),
      premises: hypotheses.map(h => ({
        statement: h.explanation,
        confidence: h.likelihood
      }))
    };
  }

  /**
   * Occam's Razor: Simplest explanation is usually best.
   */
  simplestExplanation(observation: string, candidates: string[]): ReasoningResult {
    const simplest = candidates[0]; // Assume first is already sorted by complexity

    return {
      type: 'ABDUCTIVE_OCCAM',
      conclusion: simplest,
      reasoning: `
Occam's Razor:
  - Observation: ${observation}
  - Candidates (sorted by complexity):
${candidates.map((c, i) => `    ${i + 1}. ${c}`).join('\n')}
  - Simplest: "${simplest}"
Principle: Do not multiply hypotheses beyond necessity.
Warning: Simplicity ≠ truth. But it's a good epistemic heuristic.
      `,
      confidence: 0.80,
      premises: candidates.map(c => ({ statement: c, confidence: 0.7 }))
    };
  }
}

// ============================================================================
// CAUSAL REASONING: Pearl do-Calculus
// ============================================================================

export class CausalReasoner {
  /**
   * Do-Calculus: What happens if we intervene on variable X?
   * Distinction between observation P(Y|X=x) and intervention do(X=x)
   */
  reason(model: CausalModel, intervention: string, target: string): ReasoningResult {
    const matches = model.relationships.filter(
      r => r.from.toLowerCase().includes(intervention.toLowerCase()) ||
           r.to.toLowerCase().includes(intervention.toLowerCase())
    );

    const directEffect = matches.filter(r => r.from.toLowerCase().includes(intervention.toLowerCase()));
    const confounding = matches.filter(r => r.from !== intervention && r.to === target);

    return {
      type: 'CAUSAL',
      conclusion: `do(${intervention}) has ${directEffect.length} direct effect(s) on outcomes`,
      reasoning: `
Causal Do-Calculus (Pearl):
  - Variable: ${intervention}
  - Target outcome: ${target}
  - Causal model has ${model.relationships.length} relationships
  
Direct effects of do(${intervention}):
${directEffect.map(r => `  → ${r.from} → ${r.to} (strength: ${r.strength})`).join('\n')}

Confounding variables (non-causal associations):
${confounding.length > 0 ? confounding.map(r => `  ⚠ ${r.from} → ${r.to}`).join('\n') : '  None detected'}

Implication: Intervening on ${intervention} will affect ${target}.
Caveat: Causal models must be correctly specified to be valid.
      `,
      confidence: directEffect.length > 0 ? 0.85 : 0.50,
      premises: model.relationships.map(r => ({
        statement: `${r.from} → ${r.to}`,
        confidence: r.strength
      }))
    };
  }

  /**
   * Reverse causality check: Could it go the other way?
   */
  reverseCausalityCheck(proposed: string, alternative: string): ReasoningResult {
    return {
      type: 'CAUSAL_REVERSE_CHECK',
      conclusion: `Bidirectional causality possible; temporal order needed.`,
      reasoning: `
Reverse Causality Check:
  - Proposed: ${proposed}
  - Alternative: ${alternative}
  
Critical question: Which comes first?
  - If ${proposed} happened first → probable causal chain
  - If ${alternative} happened first → might be reverse causality

Example: Wealth → Education? Or Education → Wealth?
  Event sequence determines causal direction.
  
Method to resolve: Check temporal precedence. Correlations alone don't establish causality.
      `,
      confidence: 0.60, // Inherently uncertain without temporal data
      premises: [
        { statement: proposed, confidence: 0.70 },
        { statement: alternative, confidence: 0.70 }
      ]
    };
  }
}

// ============================================================================
// COUNTERFACTUAL REASONING: "What if?"
// ============================================================================

export class CounterfactualReasoner {
  /**
   * Reasoning about hypothetical scenarios.
   * "If X had not happened, would Y occur?"
   */
  reason(
    actualFact: string,
    counterfactualScenario: string,
    consequence: string
  ): ReasoningResult {
    return {
      type: 'COUNTERFACTUAL',
      conclusion: `If ${counterfactualScenario}, then ${consequence}`,
      reasoning: `
Counterfactual Reasoning:
  - Actual fact: ${actualFact}
  - Counterfactual: If instead ${counterfactualScenario}
  - Hypothetical consequence: ${consequence}

Use cases:
  - Causal inference: "Would patient survive without treatment?"
  - Blame assessment: "Would accident happen without negligence?"
  - Planning: "If strategy changes, what happens?"
  
Limitation: Counterfactuals are harder to verify. Ground in causal models when possible.
      `,
      confidence: 0.65, // Lower confidence for unobserved scenarios
      premises: [
        { statement: actualFact, confidence: 0.95 },
        { statement: counterfactualScenario, confidence: 0.50 }
      ]
    };
  }

  /**
   * Simpson's Paradox: Trend reverses when stratified.
   * Counterfactual check for hidden variables.
   */
  simpsonsParadox(overallTrend: string, stratifiedTrend: string): ReasoningResult {
    return {
      type: 'COUNTERFACTUAL_SIMPSON',
      conclusion: `Confounding variable detected. Stratified analysis differs from aggregate.`,
      reasoning: `
Simpson's Paradox:
  - Overall trend: ${overallTrend}
  - When stratified: ${stratifiedTrend}
  
What happened: A hidden variable reverses the apparent direction.

Example: Medicine A has higher success rate overall.
  But when stratified by disease severity:
  - Mild cases: Medicine B better
  - Severe cases: Medicine B better
  Paradox resolved: A was given mostly to mild cases.

Lesson: Always stratify by potential confounders. Aggregate statistics lie.
      `,
      confidence: 0.90,
      premises: [
        { statement: overallTrend, confidence: 0.85 },
        { statement: stratifiedTrend, confidence: 0.85 }
      ]
    };
  }
}

// ============================================================================
// ANALOGICAL REASONING: Structure Mapping
// ============================================================================

export class AnalogyReasoner {
  /**
   * Reasoning by analogy: Transfer knowledge from known domain to new domain.
   * Structure: A is to B as C is to D
   */
  reason(
    knownDomain: { source: string; property: string; outcome: string },
    newDomain: { target: string },
    similarity: number // 0-1, how structurally similar are the domains?
  ): ReasoningResult {
    return {
      type: 'ANALOGICAL',
      conclusion: `${newDomain.target} likely has similar property/outcome.`,
      reasoning: `
Analogical Reasoning:
  - Known domain: ${knownDomain.source}
    Property: ${knownDomain.property}
    Outcome: ${knownDomain.outcome}
  - New domain: ${newDomain.target}
  - Structural similarity: ${(similarity * 100).toFixed(1)}%

Logic:
  1. Identify relevant features in source domain
  2. Map features to target domain
  3. Transfer conclusions

Strength depends on similarity. Higher structural overlap → higher confidence.
  
Weakness: False analogies. Not all similarities are relevant.
Example: "Atoms are like solar systems" - misleading at quantum scale.
      `,
      confidence: similarity * 0.85,
      premises: [
        { statement: `Source: ${knownDomain.source}`, confidence: 0.90 },
        { statement: `Target: ${newDomain.target}`, confidence: 0.75 }
      ]
    };
  }

  /**
   * Metaphorical reasoning: Transfer schemas between domains.
   */
  metaphoricalMapping(
    sourceScheme: string,
    targetConcept: string,
    mappingQuality: number
  ): ReasoningResult {
    return {
      type: 'ANALOGICAL_METAPHOR',
      conclusion: `"${sourceScheme}" illuminates aspects of "${targetConcept}"`,
      reasoning: `
Metaphorical Reasoning:
  - Source scheme: ${sourceScheme}
  - Target concept: ${targetConcept}
  - Mapping quality: ${(mappingQuality * 100).toFixed(1)}%

Metaphors are cognitive tools that structure abstract thinking.
  "Time is money" → we "spend" time, time "runs out", time is "valuable"
  "Organization is a machine" → parts, efficiency, maintenance

Strength: Illuminates hidden structure.
Weakness: Metaphors can mislead if taken literally.
      `,
      confidence: 0.75,
      premises: [
        { statement: sourceScheme, confidence: 0.80 },
        { statement: targetConcept, confidence: 0.70 }
      ]
    };
  }
}

// ============================================================================
// DIALECTICAL REASONING: Thesis/Antithesis/Synthesis
// ============================================================================

export class DialecticReasoner {
  /**
   * Hegel/Marx dialectic: Positions clash and resolve into synthesis.
   */
  reason(
    thesis: { claim: string; evidence: string[]; strength: number },
    antithesis: { claim: string; evidence: string[]; strength: number }
  ): ReasoningResult {
    const synthesisStrength = Math.max(thesis.strength, antithesis.strength);
    const weakerClaim = thesis.strength < antithesis.strength ? thesis : antithesis;
    const strongerClaim = thesis.strength >= antithesis.strength ? thesis : antithesis;

    return {
      type: 'DIALECTICAL',
      conclusion: `Synthesis: Combine insights from both positions, acknowledging ${weakerClaim.claim}'s partial validity.`,
      reasoning: `
Dialectical Reasoning:
  - Thesis: ${thesis.claim}
    Evidence: ${thesis.evidence.join(', ')}
    Strength: ${(thesis.strength * 100).toFixed(1)}%
    
  - Antithesis: ${antithesis.claim}
    Evidence: ${antithesis.evidence.join(', ')}
    Strength: ${(antithesis.strength * 100).toFixed(1)}%

  - Synthesis: Integrate valid points from both
    The stronger position (${strongerClaim.claim}) has merit.
    But ${weakerClaim.claim} captures a real tension.
    Resolution: ${strongerClaim.claim}, BUT acknowledge ${weakerClaim.claim}.

Example: Freedom vs Security (both necessary; tension managed by law)

Method: Acknowledge contradiction, find higher-order integration.
      `,
      confidence: synthesisStrength,
      premises: [
        ...thesis.evidence.map(e => ({ statement: e, confidence: thesis.strength })),
        ...antithesis.evidence.map(e => ({ statement: e, confidence: antithesis.strength }))
      ]
    };
  }
}

// ============================================================================
// COORDINATOR
// ============================================================================

export class ReasoningEngine {
  public readonly deductive: DeductiveReasoner;
  public readonly inductive: InductiveReasoner;
  public readonly abductive: AbductiveReasoner;
  public readonly causal: CausalReasoner;
  public readonly counterfactual: CounterfactualReasoner;
  public readonly analogy: AnalogyReasoner;
  public readonly dialectic: DialecticReasoner;

  constructor() {
    this.deductive = new DeductiveReasoner();
    this.inductive = new InductiveReasoner();
    this.abductive = new AbductiveReasoner();
    this.causal = new CausalReasoner();
    this.counterfactual = new CounterfactualReasoner();
    this.analogy = new AnalogyReasoner();
    this.dialectic = new DialecticReasoner();
  }

  /**
   * Dispatch to appropriate reasoner based on problem structure.
   */
  async autoReason(problem: {
    type?: 'deductive' | 'inductive' | 'abductive' | 'causal' | 'counterfactual' | 'analogical' | 'dialectical';
    context: string;
    query: string;
    evidence?: unknown[];
  }): Promise<ReasoningResult> {
    const type = problem.type || this.detectType(problem.query);

    switch (type) {
      case 'deductive':
        return this.deductive.reason(problem.context, problem.context, problem.query);
      case 'inductive':
        return await this.inductive.reason(
          (problem.evidence || []) as Proposition[],
          problem.query
        );
      case 'abductive':
        return this.abductive.simplestExplanation(problem.query, [problem.context]);
      case 'dialectical':
        return this.dialectic.reason(
          { claim: problem.context, evidence: [], strength: 0.7 },
          { claim: problem.query, evidence: [], strength: 0.7 }
        );
      default:
        return this.abductive.simplestExplanation(problem.query, [problem.context]);
    }
  }

  private detectType(query: string): string {
    if (query.includes('if') || query.includes('then') || query.includes('therefore')) return 'deductive';
    if (query.includes('always') || query.includes('usually') || query.includes('pattern')) return 'inductive';
    if (query.includes('why') || query.includes('explain') || query.includes('likely')) return 'abductive';
    if (query.includes('cause') || query.includes('effect') || query.includes('because')) return 'causal';
    if (query.includes('if') && query.includes('had')) return 'counterfactual';
    if (query.includes('like') || query.includes('similar') || query.includes('analogy')) return 'analogical';
    if (query.includes('vs') || query.includes('both') || query.includes('but')) return 'dialectical';
    return 'abductive'; // Default
  }

  /**
   * Get all reasoning types available.
   */
  getCapabilities(): string[] {
    return [
      'DEDUCTIVE: Logical certainty (Modus Ponens)',
      'INDUCTIVE: General rules from observations (Bayesian update)',
      'ABDUCTIVE: Best explanation (Sherlock Holmes)',
      'CAUSAL: Pearl do-calculus',
      'COUNTERFACTUAL: What-if scenarios',
      'ANALOGICAL: Structure mapping',
      'DIALECTICAL: Thesis/Antithesis/Synthesis'
    ];
  }
}

export default ReasoningEngine;
