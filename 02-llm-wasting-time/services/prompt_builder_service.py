from llm import prompts


class PromptBuilderService:
    def build_clarification_prompt(self, user_query: str, profile: dict | None) -> str:
        return (
            f"{prompts.CLARIFICATION_PROMPT}\n\n"
            f"{prompts.build_clarification_user_prompt(user_query, profile)}"
        )

    def build_recommendation_prompt(
        self, user_query: str, context: dict[str, str], profile: dict | None
    ) -> str:
        return (
            f"{prompts.RECOMMENDATION_PROMPT}\n\n"
            f"{prompts.build_recommendation_user_prompt(user_query, context, profile)}"
        )
