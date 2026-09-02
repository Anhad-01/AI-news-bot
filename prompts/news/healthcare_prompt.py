HEALTHCARE_SUMMARY_PROMPT = """\
Summarize this healthcare news article in 2-3 concise sentences.
Focus on what happened or was announced, who is affected (patients, providers, or policymakers), \
and the clinical, regulatory, or public health significance.
Use only the article body; ignore navigation text, ads, related links, and boilerplate. \
Do not use an introductory phrase.

Title: {title}
URL: {url}
Article text:
{source_text}
"""
