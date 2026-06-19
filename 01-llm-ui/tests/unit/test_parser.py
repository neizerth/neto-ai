import pytest

from llm.parser import LLMParseError, parse_llm_response, strip_markdown_json


def test_parse_valid_json(valid_llm_json):
    payload = parse_llm_response(valid_llm_json)
    assert payload.upgrade_needed is True
    assert len(payload.recommendations) == 1


def test_parse_invalid_json():
    with pytest.raises(LLMParseError):
        parse_llm_response("not json")


def test_strip_markdown():
    raw = '```json\n{"upgrade_needed": false}\n```'
    assert '"upgrade_needed"' in strip_markdown_json(raw)
