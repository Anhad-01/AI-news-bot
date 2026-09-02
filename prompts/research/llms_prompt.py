LLMS_SUMMARY_PROMPT = """\
Summarize this LLM research article in 2-3 concise sentences.
Focus on the model architecture or core technique, the training approach or dataset used, \
and the key benchmark results or performance improvements over prior work.
Only use information supported by the provided text. Do not use an introductory phrase.

Title: {title}
URL: {url}
{source_label}:
{source_text}
"""
