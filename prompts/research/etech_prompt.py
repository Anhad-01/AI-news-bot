ETECH_SUMMARY_PROMPT = """\
Summarize this technology news article in 2-3 concise sentences.
Focus on the specific product, company, or development announced, the technology involved, \
and its significance for the industry or Indian tech ecosystem.
Use only the article body; ignore navigation text, ads, related links, and boilerplate. \
Do not use an introductory phrase.

Title: {title}
URL: {url}
Article text:
{source_text}
"""
