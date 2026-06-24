"""
Prompt Registry
===============
Selects prompt templates based on the global LANGUAGE setting in config.py.

Usage:
    from agent.prompts import get_prompts
    prompts = get_prompts()  # reads LANGUAGE from config
    prompt = prompts.DAILY_SCHEDULE.format(identity=..., locations=...)

Adding a new language:
    1. Create agent/prompts/xx.py with all 4 prompt templates
    2. Add "xx": xx to the _PROMPTS dict below
    3. Set LANGUAGE = "xx" in config.py
"""
from agent.prompts import en, zh

# Registry: language code → prompt module
_PROMPTS = {
    "en": en,
    "zh": zh,
}


def get_prompts(language=None):
    """
    Return the prompt module for the given language.

    Args:
        language: "en" or "zh". If None, reads from config.LANGUAGE.

    Returns:
        Module with DAILY_SCHEDULE, ACTION_DETAIL, FOCAL_POINTS, INSIGHTS.
        Falls back to English if language not found.
    """
    if language is None:
        from config import LANGUAGE
        language = LANGUAGE
    return _PROMPTS.get(language, en)
