# Test Documentation: Prompt Registry (`tests/test_prompts.py`)

## TestPromptRegistry

### test_get_prompts_en
- **Assert**: `get_prompts("en")` returns the `en` module
- **Why**: Registry maps "en" to the English prompt module

### test_get_prompts_zh
- **Assert**: `get_prompts("zh")` returns the `zh` module
- **Why**: Registry maps "zh" to the Chinese prompt module

### test_get_prompts_fallback_unknown
- **Assert**: `get_prompts("fr")` returns the `en` module
- **Why**: Unknown language codes fall back to English

### test_get_prompts_fallback_none
- **Assert**: `get_prompts("unknown_lang")` returns the `en` module
- **Why**: Any unrecognized language falls back to English

## TestEnglishPrompts

### test_has_system_prompt
- **Assert**: `en.SYSTEM_PROMPT` exists and contains "Ville"
- **Why**: English system prompt references the simulation world name

### test_has_daily_schedule
- **Assert**: `en.DAILY_SCHEDULE` exists and contains `{identity}` and `{locations}` placeholders
- **Why**: Daily schedule prompt needs identity and location variables

### test_has_action_detail
- **Assert**: `en.ACTION_DETAIL` exists and contains `{task_desc}` and `{current_time}` placeholders
- **Why**: Action detail prompt needs task and time variables

### test_has_focal_points
- **Assert**: `en.FOCAL_POINTS` exists and contains `{n}` and `{statements}` placeholders
- **Why**: Focal points prompt needs count and memory statements

### test_has_insights
- **Assert**: `en.INSIGHTS` exists and contains `{n}` placeholder
- **Why**: Insights prompt needs the count variable

### test_daily_schedule_format
- **Assert**: `.format()` with identity and locations produces valid output containing the values
- **Why**: Template variables are properly substituted

### test_action_detail_format
- **Assert**: `.format()` with all required variables produces output containing task_desc and time
- **Why**: All template variables work correctly

## TestChinesePrompts

### test_has_system_prompt
- **Assert**: `zh.SYSTEM_PROMPT` exists and contains "小镇"
- **Why**: Chinese system prompt references the simulation world name in Chinese

### test_has_daily_schedule
- **Assert**: `zh.DAILY_SCHEDULE` exists with `{identity}` placeholder
- **Why**: Chinese daily schedule uses same template variables as English

### test_has_action_detail
- **Assert**: `zh.ACTION_DETAIL` exists with `{task_desc}` placeholder
- **Why**: Chinese action detail uses same template variables

### test_has_focal_points
- **Assert**: `zh.FOCAL_POINTS` exists with `{n}` placeholder
- **Why**: Chinese focal points use same template variables

### test_has_insights
- **Assert**: `zh.INSIGHTS` exists with `{n}` placeholder
- **Why**: Chinese insights use same template variables

### test_daily_schedule_format
- **Assert**: `.format()` with Chinese text produces valid output
- **Why**: Chinese template variables are properly substituted

### test_action_detail_format
- **Assert**: `.format()` with Chinese text produces valid output
- **Why**: All Chinese template variables work correctly
