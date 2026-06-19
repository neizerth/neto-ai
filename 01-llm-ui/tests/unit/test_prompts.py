from llm.prompts import build_user_prompt


def test_build_user_prompt_contains_phone():
    prompt = build_user_prompt("iPhone 12", "gaming", 3, None)
    assert "iPhone 12" in prompt
    assert "Игры" in prompt
    assert "3" in prompt


def test_build_user_prompt_with_additional():
    prompt = build_user_prompt("iPhone 12", "gaming", 3, "Бюджет 100к")
    assert "Бюджет 100к" in prompt
