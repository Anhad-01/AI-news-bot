ML_SUMMARY_PROMPT = """\
Summarize this machine learning research article in 2-3 concise sentences.
Focus on the algorithmic novelty or theoretical contribution, the optimization insight or \
training technique introduced, and the empirical result or generalization finding reported.
Only use information supported by the provided text. Do not use an introductory phrase.

Title: {title}
URL: {url}
{source_label}:
{source_text}
"""
