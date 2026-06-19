from pydantic import BaseModel, Field, model_validator


class FollowupQuestion(BaseModel):
    id: str = Field(..., min_length=1, max_length=50)
    text: str = Field(..., min_length=5, max_length=300)
    hint: str | None = Field(default=None, max_length=200)


class ClarificationPayload(BaseModel):
    needs_clarification: bool
    questions: list[FollowupQuestion] = Field(default_factory=list)
    extracted_context: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_questions_consistency(self) -> "ClarificationPayload":
        if self.needs_clarification and not self.questions:
            raise ValueError("При needs_clarification=true нужен хотя бы один вопрос")
        if not self.needs_clarification and self.questions:
            raise ValueError("При needs_clarification=false список questions должен быть пустым")
        if self.needs_clarification and len(self.questions) > 5:
            raise ValueError("Не более 5 уточняющих вопросов за раунд")
        ids = [q.id for q in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("ID вопросов должны быть уникальными")
        return self


class AlternativeOption(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    description: str = Field(..., min_length=10, max_length=500)
    budget_estimation: str = Field(..., min_length=2, max_length=100)
    time_estimation: str = Field(..., min_length=2, max_length=100)


class RecommendationPayload(BaseModel):
    main_recommendation: str = Field(..., min_length=10, max_length=1000)
    alternatives: list[AlternativeOption] = Field(default_factory=list)
    reasoning: str = Field(..., min_length=10, max_length=1500)
    budget_estimation: str = Field(..., min_length=2, max_length=100)
    time_estimation: str = Field(..., min_length=2, max_length=100)

    @model_validator(mode="after")
    def validate_alternatives_count(self) -> "RecommendationPayload":
        if len(self.alternatives) > 5:
            raise ValueError("Не более 5 альтернатив")
        titles = [a.title for a in self.alternatives]
        if len(titles) != len(set(titles)):
            raise ValueError("Заголовки альтернатив должны быть уникальными")
        return self
