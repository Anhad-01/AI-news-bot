FINTECH_SUMMARY_PROMPT = """\
Summarize this fintech news article in 2-3 concise sentences.
Focus on the product launch, company move, or regulatory development described, \
the market or consumer impact, and any key financial figures or trends cited.
Use only the article body; ignore navigation text, ads, related links, and boilerplate. \
Do not use an introductory phrase.

Title: {title}
URL: {url}
Article text:
{source_text}
"""
