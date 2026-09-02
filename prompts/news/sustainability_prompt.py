SUSTAINABILITY_SUMMARY_PROMPT = """\
Summarize this sustainability or climate news article in 2-3 concise sentences.
Focus on the specific policy action, environmental development, or technology announcement described, \
the scale or measurable impact (emissions reductions, funding amounts, targets), and why it matters.
Use only the article body; ignore navigation text, ads, related links, and boilerplate. \
Do not use an introductory phrase.

Title: {title}
URL: {url}
Article text:
{source_text}
"""
