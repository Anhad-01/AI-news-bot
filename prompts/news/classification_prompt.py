# Skeleton — used when ArticleClassifier.classify() is implemented.
#
# Activation checklist:
#   1. Implement ArticleClassifier.classify() in services/article_classifier.py.
#   2. Uncomment the geography filter in agents/news/base_news_agent.py.
#   3. Uncomment the retry loop in agents/news/base_news_agent.py.

CLASSIFICATION_PROMPT = """\
You are classifying news article headlines as either "Indian" or "Global".

Rules:
- "Indian": the article is about India, the Indian government, Indian companies,
  events happening in India, Indian citizens, or Indian policy — even if it
  also has global context.
- "Global": the article has absolutely no connection to India.
- When in doubt, classify as "Indian". Never let an Indian story be marked as Global.

Classify the following headlines. Respond with a JSON array only —
no explanation, no markdown, just the JSON.

Headlines:
{headlines}

Required format:
[{{"index": 1, "classification": "Indian"}}, {{"index": 2, "classification": "Global"}}, ...]
"""
