"""Tests for LLM enrichment functionality."""

import json
from unittest.mock import Mock

import pytest
from anthropic import Anthropic

from agentready.learners.llm_enricher import LLMEnricher
from agentready.models import Attribute, DiscoveredSkill, Finding, Repository


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    client = Mock(spec=Anthropic)

    # Mock response
    mock_response = Mock()
    mock_response.content = [
        Mock(
            text=json.dumps(
                {
                    "skill_description": "Enhanced description from LLM",
                    "instructions": [
                        "Step 1: Do something specific",
                        "Step 2: Verify it worked",
                        "Step 3: Commit the changes",
                    ],
                    "code_examples": [
                        {
                            "file_path": "src/example.py",
                            "code": "def example():\n    pass",
                            "explanation": "This shows the pattern",
                        }
                    ],
                    "best_practices": ["Always use type hints", "Test your code"],
                    "anti_patterns": [
                        "Don't use global variables",
                        "Avoid mutable defaults",
                    ],
                }
            )
        )
    ]

    client.messages.create.return_value = mock_response
    return client


@pytest.fixture
def basic_skill():
    """Basic skill from heuristic extraction."""
    return DiscoveredSkill(
        skill_id="test-skill",
        name="Test Skill",
        description="Basic description",
        confidence=95.0,
        source_attribute_id="test_attribute",
        reusability_score=100.0,
        impact_score=50.0,
        pattern_summary="Test pattern",
        code_examples=["Basic example"],
        citations=[],
    )


@pytest.fixture
def sample_repository(tmp_path):
    """Sample repository."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()

    # Create .git directory
    (repo_path / ".git").mkdir()

    # Create a sample file
    (repo_path / "test.py").write_text("def test():\n    pass")

    return Repository(
        path=repo_path,
        name="test-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages={"Python": 1},
        total_files=1,
        total_lines=2,
    )


@pytest.fixture
def sample_finding():
    """Sample finding."""
    attr = Attribute(
        id="test_attribute",
        name="Test Attribute",
        category="Testing",
        tier=1,
        description="A test attribute",
        criteria="Must pass",
        default_weight=1.0,
    )

    return Finding(
        attribute=attr,
        status="pass",
        score=95.0,
        measured_value="passing",
        threshold="pass",
        evidence=["Test evidence 1", "Test evidence 2"],
        remediation=None,
        error_message=None,
    )


def test_enrich_skill_success(
    mock_anthropic_client, basic_skill, sample_repository, sample_finding, tmp_path
):
    """Test successful skill enrichment."""
    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(mock_anthropic_client, cache_dir=cache_dir)

    enriched = enricher.enrich_skill(basic_skill, sample_repository, sample_finding)

    # Verify API was called
    assert mock_anthropic_client.messages.create.called

    # Verify enrichment
    assert enriched.description == "Enhanced description from LLM"
    assert len(enriched.code_examples) > len(basic_skill.code_examples)


def test_enrich_skill_uses_cache(
    mock_anthropic_client, basic_skill, sample_repository, sample_finding, tmp_path
):
    """Test that second enrichment uses cache."""
    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(mock_anthropic_client, cache_dir=cache_dir)

    # First call
    enricher.enrich_skill(basic_skill, sample_repository, sample_finding)
    first_call_count = mock_anthropic_client.messages.create.call_count

    # Second call (should use cache)
    enricher.enrich_skill(basic_skill, sample_repository, sample_finding)
    second_call_count = mock_anthropic_client.messages.create.call_count

    # Verify cache was used
    assert second_call_count == first_call_count


def test_enrich_skill_api_error_fallback(
    basic_skill, sample_repository, sample_finding, tmp_path
):
    """Test fallback to original skill on API error."""
    client = Mock(spec=Anthropic)
    client.messages.create.side_effect = Exception("API Error")

    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(client, cache_dir=cache_dir)

    enriched = enricher.enrich_skill(basic_skill, sample_repository, sample_finding)

    # Should return original skill
    assert enriched.skill_id == basic_skill.skill_id
    assert enriched.description == basic_skill.description


def test_enrich_skill_no_cache(
    mock_anthropic_client, basic_skill, sample_repository, sample_finding, tmp_path
):
    """Test enrichment with caching disabled."""
    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(mock_anthropic_client, cache_dir=cache_dir)

    # First call with use_cache=False
    enricher.enrich_skill(
        basic_skill, sample_repository, sample_finding, use_cache=False
    )
    first_count = mock_anthropic_client.messages.create.call_count

    # Second call with use_cache=False (should call API again)
    enricher.enrich_skill(
        basic_skill, sample_repository, sample_finding, use_cache=False
    )
    second_count = mock_anthropic_client.messages.create.call_count

    # Should have called API twice
    assert second_count == first_count + 1


def test_enrich_skill_custom_model(
    basic_skill, sample_repository, sample_finding, tmp_path
):
    """Test enricher with custom model."""
    client = Mock(spec=Anthropic)
    mock_response = Mock()
    mock_response.content = [
        Mock(text='{"skill_description": "Test", "instructions": []}')
    ]
    client.messages.create.return_value = mock_response

    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(client, cache_dir=cache_dir, model="claude-3-opus-20240229")

    enricher.enrich_skill(basic_skill, sample_repository, sample_finding)

    # Verify correct model was used
    call_args = client.messages.create.call_args
    assert call_args[1]["model"] == "claude-3-opus-20240229"


def test_enrich_skill_empty_evidence(
    mock_anthropic_client, basic_skill, sample_repository, tmp_path
):
    """Test enrichment with empty evidence."""
    attr = Attribute(
        id="test",
        name="Test",
        category="Test",
        tier=1,
        description="Test",
        criteria="Test",
        default_weight=1.0,
    )
    finding_no_evidence = Finding(
        attribute=attr,
        status="pass",
        score=100.0,
        measured_value="pass",
        threshold="pass",
        evidence=[],  # Empty evidence
        remediation=None,
        error_message=None,
    )

    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(mock_anthropic_client, cache_dir=cache_dir)

    # Should handle empty evidence gracefully
    enriched = enricher.enrich_skill(
        basic_skill, sample_repository, finding_no_evidence
    )

    assert enriched is not None


def test_enrich_skill_none_evidence(
    mock_anthropic_client, basic_skill, sample_repository, tmp_path
):
    """Test enrichment with None evidence."""
    attr = Attribute(
        id="test",
        name="Test",
        category="Test",
        tier=1,
        description="Test",
        criteria="Test",
        default_weight=1.0,
    )
    finding_none_evidence = Finding(
        attribute=attr,
        status="pass",
        score=100.0,
        measured_value="pass",
        threshold="pass",
        evidence=None,  # None evidence
        remediation=None,
        error_message=None,
    )

    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(mock_anthropic_client, cache_dir=cache_dir)

    # Should handle None evidence gracefully
    enriched = enricher.enrich_skill(
        basic_skill, sample_repository, finding_none_evidence
    )

    assert enriched is not None


def test_enrich_skill_rate_limit_retry(
    basic_skill, sample_repository, sample_finding, tmp_path
):
    """Test rate limit error with retry."""
    from unittest.mock import patch

    from anthropic import RateLimitError

    client = Mock(spec=Anthropic)

    # First call raises rate limit, second succeeds
    # Create mock response for RateLimitError
    mock_response = Mock()
    mock_response.status_code = 429
    rate_limit_error = RateLimitError("Rate limit", response=mock_response, body=None)
    rate_limit_error.retry_after = 1  # 1 second retry

    success_response = Mock()
    success_response.content = [
        Mock(text='{"skill_description": "Success", "instructions": []}')
    ]

    client.messages.create.side_effect = [rate_limit_error, success_response]

    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(client, cache_dir=cache_dir)

    # Mock sleep to avoid actual delay
    with patch("agentready.learners.llm_enricher.sleep"):
        enriched = enricher.enrich_skill(basic_skill, sample_repository, sample_finding)

    # Should eventually succeed after retry
    assert enriched.description == "Success"
    # Verify both calls were made
    assert client.messages.create.call_count == 2


def test_enrich_skill_api_error_specific(
    basic_skill, sample_repository, sample_finding, tmp_path
):
    """Test specific API error handling."""
    from anthropic import APIError

    client = Mock(spec=Anthropic)
    # Create mock request for APIError
    mock_request = Mock()
    client.messages.create.side_effect = APIError(
        "API Error", request=mock_request, body=None
    )

    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(client, cache_dir=cache_dir)

    enriched = enricher.enrich_skill(basic_skill, sample_repository, sample_finding)

    # Should fallback to original skill
    assert enriched == basic_skill


def test_enrich_skill_invalid_json_response(
    basic_skill, sample_repository, sample_finding, tmp_path
):
    """Test handling of invalid JSON in response."""
    client = Mock(spec=Anthropic)
    mock_response = Mock()
    mock_response.content = [Mock(text="Not valid JSON{")]
    client.messages.create.return_value = mock_response

    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(client, cache_dir=cache_dir)

    # Should fallback to original skill on parse error
    enriched = enricher.enrich_skill(basic_skill, sample_repository, sample_finding)

    assert enriched.skill_id == basic_skill.skill_id


def test_enrich_skill_partial_json_response(
    basic_skill, sample_repository, sample_finding, tmp_path
):
    """Test handling of partial/incomplete JSON response."""
    client = Mock(spec=Anthropic)
    mock_response = Mock()
    # Missing required fields
    mock_response.content = [Mock(text='{"skill_description": "Partial"}')]
    client.messages.create.return_value = mock_response

    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(client, cache_dir=cache_dir)

    # Should handle gracefully (may use partial or fallback)
    enriched = enricher.enrich_skill(basic_skill, sample_repository, sample_finding)

    assert enriched is not None


def test_llm_enricher_init_default_cache(mock_anthropic_client):
    """Test LLMEnricher initialization with default cache directory."""
    enricher = LLMEnricher(mock_anthropic_client)

    assert enricher.client == mock_anthropic_client
    assert enricher.model == "claude-sonnet-4-5-20250929"
    assert enricher.cache is not None


def test_llm_enricher_init_custom_cache(mock_anthropic_client, tmp_path):
    """Test LLMEnricher initialization with custom cache directory."""
    custom_cache = tmp_path / "custom-cache"
    enricher = LLMEnricher(mock_anthropic_client, cache_dir=custom_cache)

    assert enricher.cache is not None


def test_merge_enrichment(mock_anthropic_client, basic_skill, tmp_path):
    """Test merging enrichment data into skill."""
    enricher = LLMEnricher(mock_anthropic_client, cache_dir=tmp_path)

    enrichment_data = {
        "skill_description": "Enhanced description",
        "instructions": ["Step 1", "Step 2"],
        "code_examples": [
            {"file_path": "test.py", "code": "code", "explanation": "ex"}
        ],
        "best_practices": ["Practice 1"],
        "anti_patterns": ["AntiPattern 1"],
    }

    enriched = enricher._merge_enrichment(basic_skill, enrichment_data)

    assert enriched.description == "Enhanced description"
    assert "Step 1" in str(enriched.code_examples) or "Step 1" in str(
        enriched.citations
    )


def test_call_claude_api_builds_prompt(
    mock_anthropic_client, basic_skill, sample_repository, sample_finding, tmp_path
):
    """Test that _call_claude_api builds correct prompt."""
    enricher = LLMEnricher(mock_anthropic_client, cache_dir=tmp_path)

    enricher._call_claude_api(
        basic_skill, sample_finding, sample_repository, "code samples"
    )

    # Verify API was called with proper arguments
    assert mock_anthropic_client.messages.create.called
    call_args = mock_anthropic_client.messages.create.call_args

    # Check prompt contains key information
    messages = call_args[1]["messages"]
    assert len(messages) > 0
    prompt = messages[0]["content"]
    assert "test-repo" in prompt.lower() or "test" in prompt.lower()


def test_enrich_skill_initializes_code_sampler(
    mock_anthropic_client, basic_skill, sample_repository, sample_finding, tmp_path
):
    """Test that enrich_skill initializes code sampler."""
    cache_dir = tmp_path / "cache"
    enricher = LLMEnricher(mock_anthropic_client, cache_dir=cache_dir)

    # Initially None
    assert enricher.code_sampler is None

    enricher.enrich_skill(basic_skill, sample_repository, sample_finding)

    # Should be initialized after enrichment
    assert enricher.code_sampler is not None
