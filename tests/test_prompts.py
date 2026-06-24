import pytest
from agent.prompts import get_prompts
from agent.prompts import en, zh


class TestPromptRegistry:
    def test_get_prompts_en(self):
        prompts = get_prompts("en")
        assert prompts is en

    def test_get_prompts_zh(self):
        prompts = get_prompts("zh")
        assert prompts is zh

    def test_get_prompts_fallback_unknown(self):
        prompts = get_prompts("fr")
        assert prompts is en

    def test_get_prompts_fallback_none(self):
        prompts = get_prompts("unknown_lang")
        assert prompts is en


class TestEnglishPrompts:
    def test_has_system_prompt(self):
        assert hasattr(en, "SYSTEM_PROMPT")
        assert "Ville" in en.SYSTEM_PROMPT

    def test_has_daily_schedule(self):
        assert hasattr(en, "DAILY_SCHEDULE")
        assert "{identity}" in en.DAILY_SCHEDULE
        assert "{locations}" in en.DAILY_SCHEDULE

    def test_has_action_detail(self):
        assert hasattr(en, "ACTION_DETAIL")
        assert "{task_desc}" in en.ACTION_DETAIL
        assert "{current_time}" in en.ACTION_DETAIL

    def test_has_focal_points(self):
        assert hasattr(en, "FOCAL_POINTS")
        assert "{n}" in en.FOCAL_POINTS
        assert "{statements}" in en.FOCAL_POINTS

    def test_has_insights(self):
        assert hasattr(en, "INSIGHTS")
        assert "{n}" in en.INSIGHTS

    def test_daily_schedule_format(self):
        result = en.DAILY_SCHEDULE.format(
            identity="I am test.",
            locations="loc1\nloc2"
        )
        assert "test" in result
        assert "loc1" in result

    def test_action_detail_format(self):
        result = en.ACTION_DETAIL.format(
            identity="I am test.",
            task_desc="cooking",
            current_location="kitchen",
            current_time="10:00",
            locations="loc1"
        )
        assert "cooking" in result
        assert "10:00" in result


class TestChinesePrompts:
    def test_has_system_prompt(self):
        assert hasattr(zh, "SYSTEM_PROMPT")
        assert "小镇" in zh.SYSTEM_PROMPT

    def test_has_daily_schedule(self):
        assert hasattr(zh, "DAILY_SCHEDULE")
        assert "{identity}" in zh.DAILY_SCHEDULE

    def test_has_action_detail(self):
        assert hasattr(zh, "ACTION_DETAIL")
        assert "{task_desc}" in zh.ACTION_DETAIL

    def test_has_focal_points(self):
        assert hasattr(zh, "FOCAL_POINTS")
        assert "{n}" in zh.FOCAL_POINTS

    def test_has_insights(self):
        assert hasattr(zh, "INSIGHTS")
        assert "{n}" in zh.INSIGHTS

    def test_daily_schedule_format(self):
        result = zh.DAILY_SCHEDULE.format(
            identity="我是测试。",
            locations="地点1\n地点2"
        )
        assert "测试" in result
        assert "地点1" in result

    def test_action_detail_format(self):
        result = zh.ACTION_DETAIL.format(
            identity="我是测试。",
            task_desc="做饭",
            current_location="厨房",
            current_time="10:00",
            locations="地点1"
        )
        assert "做饭" in result
        assert "10:00" in result
