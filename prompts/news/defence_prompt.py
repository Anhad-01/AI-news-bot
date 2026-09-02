DEFENCE_SUMMARY_PROMPT = """\
Summarize this defence and military news article in 2-3 concise sentences.
Focus on the specific event or development that occurred, the key nations or actors involved, \
and the geopolitical or strategic significance.
Use only the article body; ignore navigation text, ads, related links, and boilerplate. \
Do not use an introductory phrase.

Title: {title}
URL: {url}
Article text:
{source_text}
"""
