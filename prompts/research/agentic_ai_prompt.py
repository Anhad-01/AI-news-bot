AGENTIC_AI_SUMMARY_PROMPT = """\
Summarize this agentic AI research article in 2-3 concise sentences.
Focus on the agent framework or architecture proposed, the task or environment it operates in \
(e.g. tool use, multi-step reasoning, web navigation), and the key capability demonstrated or benchmark achieved.
Only use information supported by the provided text. Do not use an introductory phrase.

Title: {title}
URL: {url}
{source_label}:
{source_text}
"""
