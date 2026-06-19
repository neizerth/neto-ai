"""
Unit-тесты PromptBuilderService.

Спецификация: docs/architecture.md, docs/models.md
"""

import pytest

from services.prompt_builder_service import PromptBuilderService


@pytest.fixture
def builder():
    return PromptBuilderService()


class TestPromptBuilderService:
    def test_clarification_prompt_contains_user_query(self, builder, sample_user_query):
        prompt = builder.build_clarification_prompt(sample_user_query, profile=None)
        assert sample_user_query in prompt

    def test_clarification_prompt_includes_profile_when_given(
        self, builder, sample_user_query, sample_profile_payload
    ):
        prompt = builder.build_clarification_prompt(
            sample_user_query, profile=sample_profile_payload
        )
        assert "medium" in prompt or "кино" in prompt

    def test_recommendation_prompt_contains_context(
        self, builder, sample_user_query, sample_profile_payload
    ):
        context = {"budget": "До 5000 ₽", "company": "С другом"}
        prompt = builder.build_recommendation_prompt(
            sample_user_query, context=context, profile=sample_profile_payload
        )
        assert "До 5000 ₽" in prompt
        assert "С другом" in prompt

    def test_recommendation_prompt_contains_user_query(
        self, builder, sample_user_query
    ):
        prompt = builder.build_recommendation_prompt(
            sample_user_query, context={}, profile=None
        )
        assert sample_user_query in prompt
