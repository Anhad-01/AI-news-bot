COMPUTER_VISION_SUMMARY_PROMPT = """\
Summarize this computer vision research article in 2-3 concise sentences.
Focus on the visual task addressed (e.g. object detection, image segmentation, generation, \
3D reconstruction), the dataset or benchmark used, and the key metric improvement or novel finding.
Only use information supported by the provided text. Do not use an introductory phrase.

Title: {title}
URL: {url}
{source_label}:
{source_text}
"""
