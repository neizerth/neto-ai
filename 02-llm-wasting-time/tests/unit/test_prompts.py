"""
Unit-тесты шаблонов промптов.

Спецификация: docs/architecture.md
"""

import pytest

from llm import prompts


class TestPromptsModule:
    def test_system_prompt_is_non_empty(self):
        assert prompts.SYSTEM_PROMPT
        assert len(prompts.SYSTEM_PROMPT) > 50

    def test_clarification_prompt_is_non_empty(self):
        assert prompts.CLARIFICATION_PROMPT
        assert "уточн" in prompts.CLARIFICATION_PROMPT.lower()

    def test_recommendation_prompt_is_non_empty(self):
        assert prompts.RECOMMENDATION_PROMPT
        assert "рекоменд" in prompts.RECOMMENDATION_PROMPT.lower()

    def test_build_clarification_user_prompt(self, sample_user_query):
        result = prompts.build_clarification_user_prompt(
            sample_user_query, profile=None
        )
        assert sample_user_query in result

    def test_build_recommendation_user_prompt(self, sample_user_query):
        context = {"budget": "5000 ₽"}
        result = prompts.build_recommendation_user_prompt(
            sample_user_query, context=context, profile=None
        )
        assert sample_user_query in result
        assert "5000" in result
