POLITICS_SUMMARY_PROMPT = """\
Summarize this politics news article in 2-3 concise sentences.
Focus on the key event or decision that took place, the principal figures or institutions involved, \
and the political or policy implications.
Use only the article body; ignore navigation text, ads, related links, and boilerplate. \
Do not use an introductory phrase.

Title: {title}
URL: {url}
Article text:
{source_text}
"""
