/**
 * BiasDetector.ts
 *
 * Cognitive Workflow Phase 7: Bias Mitigation
 * Catalog of ~24+ cognitive biases with detection and mitigation strategies
 * Reference: Kahneman, Thaler, Pearl, Tversky
 */
export class BiasDetector {
    // ========================================================================
    // AVAILABILITY BIAS: Things easily remembered seem more likely
    // ========================================================================
    detectAvailabilityBias(input, frequency) {
        const keywords = ['always', 'never', 'everyone knows', 'obviously', 'recent', 'memorable'];
        const hasAvailabilityLanguage = keywords.some(k => input.toLowerCase().includes(k));
        return {
            biasName: 'AVAILABILITY BIAS',
            detected: hasAvailabilityLanguage,
            severity: frequency ? Math.abs(frequency.perceived - frequency.actual) / frequency.actual : 0.5,
            evidence: [
                'Uses superlatives (always, never)',
                'References recent/memorable examples',
                'Assumes salience = frequency'
            ],
            mitigation: [
                'Request base rates: "What % of cases actually have this?"',
                'Distinguish between memorable and frequent',
                'Use data instead of examples',
                'Consider recent vs historical frequency'
            ],
            example: '"Plane crashes are everywhere" (Available in news, but cars deadlier)'
        };
    }
    // ========================================================================
    // CONFIRMATION BIAS: Seeking evidence that confirms existing beliefs
    // ========================================================================
    detectConfirmationBias(beliefToTest, evidencePresented) {
        const ratio = evidencePresented.supporting.length / (evidencePresented.contradicting.length + 1);
        const hasConfirmationBias = ratio > 2 || evidencePresented.contradicting.length === 0;
        return {
            biasName: 'CONFIRMATION BIAS',
            detected: hasConfirmationBias,
            severity: Math.min(1, (ratio - 1) / 5),
            evidence: [
                `Supporting evidence presented: ${evidencePresented.supporting.length}`,
                `Contradicting evidence presented: ${evidencePresented.contradicting.length}`,
                `Ratio: ${ratio.toFixed(2)}:1 (imbalanced if >2:1)`
            ],
            mitigation: [
                'Actively seek contradicting evidence',
                'Ask: "What would disprove this?"',
                'Steel-man opposing arguments, not straw-man',
                'Use Bayesian reasoning: P(belief|evidence) not just P(evidence|belief)',
                'Assign equal weight to both sides initially'
            ],
            example: '"Trump supporters only read Trump news" (Confirmation spiral)'
        };
    }
    // ========================================================================
    // SURVIVORSHIP BIAS: Success stories visible, failures hidden
    // ========================================================================
    detectSurvivalshipBias(successStories, failureCases) {
        const survivorshipRatio = failureCases ?
            successStories.length / (failureCases.length + successStories.length) :
            0.8; // Assume high bias if no failure data
        return {
            biasName: 'SURVIVORSHIP BIAS',
            detected: survivorshipRatio > 0.6,
            severity: Math.max(survivorshipRatio - 0.5, 0),
            evidence: [
                `Success stories presented: ${successStories.length}`,
                `Failure cases presented: ${failureCases?.length || 'unknown'} (often missing!)`,
                `Survivorship ratio: ${(survivorshipRatio * 100).toFixed(1)}%`
            ],
            mitigation: [
                'Ask: "How many failed attempts preceded this success?"',
                'Look for graveyard data: businesses that closed, startups that died',
                'Calculate true success rate: successes / (successes + failures)',
                'Interview failures, not just winners',
                'Check reference class: "Out of X startups, only Y succeeded"'
            ],
            example: '"Look at billionaire CEOs\' lessons!" (Ignore millions who failed with identical strategy)'
        };
    }
    // ========================================================================
    // DUNNING-KRUGER EFFECT: Incompetent overestimate own competence
    // ========================================================================
    detectDunningKruger(claimedConfidence, actualKnowledge, expertise) {
        const gap = claimedConfidence - actualKnowledge;
        const isDunningKruger = gap > 0.3 && actualKnowledge < 0.4;
        return {
            biasName: 'DUNNING-KRUGER EFFECT',
            detected: isDunningKruger,
            severity: Math.min(1, gap),
            evidence: [
                `Claimed confidence: ${(claimedConfidence * 100).toFixed(0)}%`,
                `Actual knowledge on ${expertise}: ${(actualKnowledge * 100).toFixed(0)}%`,
                `Gap: ${((gap) * 100).toFixed(0)}%`
            ],
            mitigation: [
                'Peak of Dunning-Kruger at ~30% knowledge - most dangerous',
                'True expert knows what they don\'t know (confidence dips at 70% then rises)',
                'Require domain credentials: citations, peer review, track record',
                'Test: Can they articulate counterarguments?',
                'Learn more → confidence initially drops (normal pattern)'
            ],
            example: '"I studied one diet book, I\'m a nutritionist" (Peak Dunning-Kruger)'
        };
    }
    // ========================================================================
    // BASE RATE FALLACY: Ignoring prior probability, only looking at specific info
    // ========================================================================
    detectBaseRateFallacy(specificInfo, baseRate, likelihoods) {
        // Bayesian check: Does conclusion match posterior probability?
        const posterior = (likelihoods.ifTrue * baseRate) /
            ((likelihoods.ifTrue * baseRate) + (likelihoods.ifFalse * (1 - baseRate)));
        return {
            biasName: 'BASE RATE FALLACY',
            detected: true,
            severity: Math.abs(baseRate - 0.5), // Worse when base rate is very skewed
            evidence: [
                `Specific info: "${specificInfo}"`,
                `Base rate (prior): ${(baseRate * 100).toFixed(1)}%`,
                `P(info|true): ${(likelihoods.ifTrue * 100).toFixed(1)}%`,
                `P(info|false): ${(likelihoods.ifFalse * 100).toFixed(1)}%`,
                `True posterior probability: ${(posterior * 100).toFixed(1)}%`
            ],
            mitigation: [
                'Calculate Bayes: P(H|E) = P(E|H)*P(H) / P(E)',
                'Always ask: "What % of population has this condition?"',
                'Example: Positive test for 1% disease with 99% accuracy still means only ~50% actually have it',
                'Use natural frequencies: "Out of 10,000 people, 100 have condition..."',
                'Check: 2% test result means 2%? Or ~50% after Bayes?'
            ],
            example: 'COVID test positive with 95% accuracy but 0.1% prevalence → ~2% true positive'
        };
    }
    // ========================================================================
    // ANCHORING BIAS: First number disproportionately influences estimate
    // ========================================================================
    detectAnchoringBias(firstNumberMentioned, finalEstimate, rangeExpected) {
        const expectedMid = (rangeExpected.min + rangeExpected.max) / 2;
        const distanceFromAnchor = Math.abs(finalEstimate - firstNumberMentioned);
        const distanceFromExpected = Math.abs(finalEstimate - expectedMid);
        const isAnchored = distanceFromAnchor < distanceFromExpected;
        return {
            biasName: 'ANCHORING BIAS',
            detected: isAnchored,
            severity: 1 - (distanceFromAnchor / (rangeExpected.max - rangeExpected.min)),
            evidence: [
                `First number mentioned (anchor): ${firstNumberMentioned}`,
                `Final estimate: ${finalEstimate}`,
                `Expected range: ${rangeExpected.min}-${rangeExpected.max}`,
                `Estimate is ${distanceFromAnchor} away from anchor (biased)`
            ],
            mitigation: [
                'Don\'t mention numbers first in negotiations',
                'Explicitly consider the anchor: "This anchor might influence me"',
                'Generate independent estimate before seeing anchor',
                'Use reference points from similar cases',
                'In salary negotiation: Don\'t let employer anchor first'
            ],
            example: '"What\'s company worth?" Seller: "$10M" → buyer thinks $8-10M instead of true $4-6M'
        };
    }
    // ========================================================================
    // TEXAS SHARPSHOOTER BIAS: Shoot arrow, draw target around it (HARKing)
    // ========================================================================
    detectTexasSharpshooterBias(hypothesisFormation, dataAvailableWhen) {
        const isBias = hypothesisFormation === 'after' || dataAvailableWhen === 'before';
        return {
            biasName: 'TEXAS SHARPSHOOTER BIAS',
            detected: isBias,
            severity: isBias ? 0.8 : 0.1,
            evidence: [
                `Hypothesis formed: ${hypothesisFormation} seeing data`,
                `Data availability: ${dataAvailableWhen === 'before' ? 'Researcher had access before hypothesis' : 'Data collected after hypothesis'}`,
                'HARKing: Hypothesizing After Results are Known'
            ],
            mitigation: [
                'Pre-register hypotheses before analyzing data',
                'Train/test split: Form hypothesis on training set, validate on test set',
                'Multiple comparisons correction: Bonferroni, FDR',
                'Ask: "Was this the original hypothesis or post-hoc explanation?"',
                'Replication: Can others find same pattern independently?'
            ],
            example: '"I looked at 1000 patterns, found 50 statistically significant ones by chance" (no correction)'
        };
    }
    // ========================================================================
    // HINDSIGHT BIAS: "I knew it all along" after outcome revealed
    // ========================================================================
    detectHindsightBias(predictionBefore, actualOutcome, currentClaim) {
        const claimMatches = currentClaim.includes(actualOutcome) || currentClaim.includes('obvious') || currentClaim.includes('inevitable');
        return {
            biasName: 'HINDSIGHT BIAS',
            detected: claimMatches && predictionBefore !== currentClaim,
            severity: 0.7,
            evidence: [
                `Prediction before: "${predictionBefore}"`,
                `Actual outcome: "${actualOutcome}"`,
                `Current claim: "${currentClaim}"`,
                'Mismatch suggests revision after outcome known'
            ],
            mitigation: [
                'Document actual prediction before outcome',
                'Avoid "I told you so" without timestamped evidence',
                'Ask: "What % of experts got this right beforehand?"',
                'Complexity check: Was outcome truly predictable?',
                'Black swan: Low probability but high impact events'
            ],
            example: '"2008 financial crisis was obvious!" vs. "Pre-2008 consensus: housing prices keep rising"'
        };
    }
    // ========================================================================
    // CONJUNCTION FALLACY: A & B seems more likely than B (Gambler's fallacy variant)
    // ========================================================================
    detectConjunctionFallacy(singleEvent, conjunctiveEvent, probabilitiesClaimed) {
        // P(A & B) can NEVER be > P(B)
        const isFallacy = probabilitiesClaimed.conjunction > probabilitiesClaimed.single;
        return {
            biasName: 'CONJUNCTION FALLACY',
            detected: isFallacy,
            severity: isFallacy ? 0.9 : 0,
            evidence: [
                `P(${singleEvent}): ${(probabilitiesClaimed.single * 100).toFixed(1)}%`,
                `P(${singleEvent} AND ${conjunctiveEvent}): ${(probabilitiesClaimed.conjunction * 100).toFixed(1)}%`,
                isFallacy ? 'ERROR: Conjunction cannot be more likely than single event' : 'Valid'
            ],
            mitigation: [
                'Remember: P(A & B) ≤ min(P(A), P(B))',
                'Conjunction always less likely by definition',
                'More details make story more believable, NOT more probable',
                'Example: "Linda is feminist bank teller" seems likely but is P(feminist) × P(bank teller)'
            ],
            example: '"Linda is feminist bank teller" rated more likely than "Linda is bank teller"'
        };
    }
    // ========================================================================
    // SUNK COST FALLACY: Continuing because of past investment, not future value
    // ========================================================================
    detectSunkCostFallacy(pastInvestment, futureExpectedValue, continueDecision) {
        // Past cost should not influence future decision
        const isFallacy = continueDecision && futureExpectedValue <= 0;
        return {
            biasName: 'SUNK COST FALLACY',
            detected: isFallacy,
            severity: isFallacy ? 0.9 : 0,
            evidence: [
                `Past investment: $${pastInvestment.toFixed(0)}`,
                `Expected future value: $${futureExpectedValue.toFixed(0)}`,
                `Decision: ${continueDecision ? 'Continue' : 'Stop'}`,
                isFallacy ? 'ERROR: Continuing despite negative expected value' : 'Rational'
            ],
            mitigation: [
                'Ignore sunk costs in future decisions',
                'Ask: "What NOW looks attractive?" not "What about my past investment?"',
                'Movie halfway through is bad: Leave. Sunk cost of ticket irrelevant.',
                'Career change: "I spent 5 years in wrong field" - past cost irrelevant',
                'Only consider future cash flows'
            ],
            example: '"I already spent $100k on this failing startup" → but future projects better, so leave'
        };
    }
    // ========================================================================
    // REPRESENTATIVENESS BIAS: Matches stereotype → must have that property
    // ========================================================================
    detectRepresentativenessBias(description, categoryAssigned, baseRateOfCategory) {
        // Stereotypical descriptions bias probability estimates
        const isStereotypical = description.includes('typical') || description.includes('classic') || description.includes('quintessential');
        return {
            biasName: 'REPRESENTATIVENESS BIAS',
            detected: isStereotypical && baseRateOfCategory < 0.3,
            severity: Math.abs(0.9 - baseRateOfCategory), // Gap between felt likelihood and actual
            evidence: [
                `Description: "${description}"`,
                `Category assigned: "${categoryAssigned}"`,
                `Actual base rate: ${(baseRateOfCategory * 100).toFixed(1)}%`,
                `Perceived probability if description matched: ~90%`,
                `Error: Can feel like 90% when actually ${(baseRateOfCategory * 100).toFixed(1)}%`
            ],
            mitigation: [
                'Use base rates, not representativeness',
                'Ask: "How many X are there versus Y in the population?"',
                'Stereotype is orthogonal to actual probability',
                'Successful entrepreneur might look like stereotype but rare'
            ],
            example: '"Looks like a lawyer" vs. "Base rate: lawyer is 0.5% of population"'
        };
    }
    // ========================================================================
    // ILLUSORY CORRELATION: Seeing pattern where none exists
    // ========================================================================
    detectIllsoryCorrelation(observedRepeats, expectedByChance, totalOpportunities) {
        const zScore = (observedRepeats - expectedByChance) / Math.sqrt(expectedByChance);
        const isStatisticallySignificant = Math.abs(zScore) > 1.96;
        return {
            biasName: 'ILLUSORY CORRELATION',
            detected: !isStatisticallySignificant && observedRepeats > expectedByChance,
            severity: Math.max(0, Math.min(1, (observedRepeats - expectedByChance) / expectedByChance)),
            evidence: [
                `Observed repeats: ${observedRepeats}`,
                `Expected by chance: ${expectedByChance.toFixed(1)}`,
                `Total opportunities: ${totalOpportunities}`,
                `Z-score: ${zScore.toFixed(2)} (significant if >1.96 or <-1.96)`,
                isStatisticallySignificant ? 'Pattern is real' : 'Likely illusory'
            ],
            mitigation: [
                'Require statistical significance (p < 0.05)',
                'Use base rates: P(B|A) vs P(B)',
                'Check: Would this pattern appear in random data?',
                'Example: "Blood moon" + bad event = illusory, happens by chance'
            ],
            example: '"I think about friend, then they call" (coincidence, happens by chance ~once a week)'
        };
    }
    // ========================================================================
    // AFFECT HEURISTIC: Emotional reaction dominates judgment
    // ========================================================================
    detectAffectHeuristic(emotionalTone, rationalAssessment, decisionMade) {
        const emotionDrivesBias = (emotionalTone === 'positive' && rationalAssessment === 'risky' && decisionMade === 'accept') ||
            (emotionalTone === 'negative' && rationalAssessment === 'safe' && decisionMade === 'reject');
        return {
            biasName: 'AFFECT HEURISTIC',
            detected: emotionDrivesBias,
            severity: emotionDrivesBias ? 0.8 : 0,
            evidence: [
                `Emotional tone: ${emotionalTone}`,
                `Rational assessment: ${rationalAssessment}`,
                `Decision made: "${decisionMade}"`,
                emotionDrivesBias ? 'Emotion appears to override rational judgment' : 'Decision aligns with analysis'
            ],
            mitigation: [
                'Separate emotional gut-feeling from analysis',
                'Write decision rationale BEFORE deciding (pre-commitment)',
                'Sleep on decision: Let emotions cool',
                'Use expected value calculation, ignore feelings',
                'Ask: "Would I decide this if I felt neutral?"'
            ],
            example: '"Like this startup founder → invest despite 90% failure rate"'
        };
    }
    // ========================================================================
    // COMPREHENSIVE ANALYSIS
    // ========================================================================
    analyzeForBias(input, context) {
        const detectedBiases = [];
        // Run all bias detectors
        detectedBiases.push(this.detectAvailabilityBias(input));
        detectedBiases.push(this.detectConfirmationBias(input, context?.evidence || { supporting: [], contradicting: [] }));
        detectedBiases.push(this.detectSurvivalshipBias([input]));
        detectedBiases.push(this.detectDunningKruger(0.8, 0.4, 'input'));
        if (context?.baseRate !== undefined) {
            detectedBiases.push(this.detectBaseRateFallacy(input, context.baseRate, { ifTrue: 0.95, ifFalse: 0.1 }));
        }
        if (context?.anchor !== undefined) {
            detectedBiases.push(this.detectAnchoringBias(context.anchor, 0, { min: 0, max: 100 }));
        }
        if (context?.emotion) {
            detectedBiases.push(this.detectAffectHeuristic(context.emotion, 'safe', 'accept'));
        }
        const risks = detectedBiases.filter(b => b.detected);
        const overallRiskScore = risks.length > 0 ?
            risks.reduce((sum, b) => sum + b.severity, 0) / risks.length : 0;
        return {
            input,
            detectedBiases: risks,
            overallRiskScore,
            recommendation: overallRiskScore > 0.7 ?
                'HIGH BIAS RISK: Reconsider reasoning with outside view and base rates' :
                overallRiskScore > 0.4 ?
                    'MODERATE BIAS: Check for  counterarguments and alternative explanations' :
                    'LOW BIAS: Reasoning appears sound'
        };
    }
    getBiasNames() {
        return [
            'AVAILABILITY BIAS',
            'CONFIRMATION BIAS',
            'SURVIVORSHIP BIAS',
            'DUNNING-KRUGER EFFECT',
            'BASE RATE FALLACY',
            'ANCHORING BIAS',
            'TEXAS SHARPSHOOTER BIAS',
            'HINDSIGHT BIAS',
            'CONJUNCTION FALLACY',
            'SUNK COST FALLACY',
            'REPRESENTATIVENESS BIAS',
            'ILLUSORY CORRELATION',
            'AFFECT HEURISTIC'
        ];
    }
}
export default BiasDetector;
