---
category: nlp
description: Summarize long texts using extractive techniques
id: SKILL-0d2e96ca8b09
name: text-summarizer
tags:
- text
- summarization
- nlp
- extractive
version: 1.0.0
---

def summarize(text, max_sentences=5):
    """Extractive text summarization using sentence scoring.
    Args:
        text: Input text to summarize
        max_sentences: Number of sentences in summary
    Returns:
        Summarized text
    """
    import re
    from collections import Counter
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) <= max_sentences:
        return text
    words = re.findall(r'\w+', text.lower())
    freq = Counter(words)
    scored = [(sum(freq[w] for w in re.findall(r'\w+', s.lower()) if w in freq) / max(len(re.findall(r'\w+', s)), 1), s) for s in sentences]
    top = sorted(scored, key=lambda x: -x[0])[:max_sentences]
    return ' '.join(s for _, s in sorted(top, key=lambda x: sentences.index(x[1])))