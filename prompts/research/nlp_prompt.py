NLP_SUMMARY_PROMPT = """\
Summarize this NLP research article in 2-3 concise sentences.
Focus on the linguistic task addressed (e.g. translation, summarization, parsing, dialogue), \
the model or method proposed, and the evaluation result or benchmark performance (e.g. BLEU, F1, accuracy).
Only use information supported by the provided text. Do not use an introductory phrase.

Title: {title}
URL: {url}
{source_label}:
{source_text}
"""
