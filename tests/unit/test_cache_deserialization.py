"""Regression tests for assessment cache deserialization.

Tests that AssessmentCache can round-trip Assessment objects through
SQLite storage, verifying the fix for the NotImplementedError in
_deserialize_assessment().
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agentready.models.assessment import Assessment
from agentready.models.attribute import Attribute
from agentready.models.citation import Citation
from agentready.models.discovered_skill import DiscoveredSkill
from agentready.models.finding import Finding, Remediation
from agentready.models.metadata import AssessmentMetadata
from agentready.models.repository import Repository
from agentready.services.assessment_cache import AssessmentCache


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repo directory for Repository validation."""
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture
def sample_attribute():
    return Attribute(
        id="test_attr",
        name="Test Attribute",
        category="Testing",
        tier=1,
        description="A test attribute",
        criteria="Must pass",
        default_weight=0.04,
    )


@pytest.fixture
def sample_citation():
    return Citation(
        source="Test Source",
        title="Test Title",
        url="https://example.com",
        relevance="Relevant for testing",
    )


@pytest.fixture
def sample_remediation(sample_citation):
    return Remediation(
        summary="Fix the issue",
        steps=["Step 1", "Step 2"],
        tools=["tool1"],
        commands=["cmd1"],
        examples=["example1"],
        citations=[sample_citation],
    )


@pytest.fixture
def sample_finding(sample_attribute, sample_remediation):
    return Finding(
        attribute=sample_attribute,
        status="pass",
        score=85.0,
        measured_value="85%",
        threshold=">80%",
        evidence=["evidence1"],
        remediation=sample_remediation,
        error_message=None,
    )


@pytest.fixture
def sample_assessment(git_repo, sample_finding):
    repo = Repository(
        path=git_repo,
        name="test-repo",
        url="https://github.com/test/repo",
        branch="main",
        commit_hash="abc123def456",
        languages={"Python": 42},
        total_files=100,
        total_lines=5000,
    )
    return Assessment(
        repository=repo,
        timestamp=datetime(2026, 3, 26, 12, 0, 0),
        overall_score=85.0,
        certification_level="Gold",
        attributes_assessed=1,
        attributes_not_assessed=0,
        attributes_total=1,
        findings=[sample_finding],
        config=None,
        duration_seconds=1.5,
    )


class TestModelFromDict:
    """Test from_dict() class methods on all models."""

    def test_citation_round_trip(self, sample_citation):
        result = Citation.from_dict(sample_citation.to_dict())
        assert result.source == sample_citation.source
        assert result.title == sample_citation.title
        assert result.url == sample_citation.url
        assert result.relevance == sample_citation.relevance

    def test_citation_without_url(self):
        c = Citation(source="S", title="T", url=None, relevance="R")
        result = Citation.from_dict(c.to_dict())
        assert result.url is None

    def test_attribute_round_trip(self, sample_attribute):
        result = Attribute.from_dict(sample_attribute.to_dict())
        assert result.id == sample_attribute.id
        assert result.tier == sample_attribute.tier
        assert result.default_weight == sample_attribute.default_weight

    def test_remediation_round_trip(self, sample_remediation):
        result = Remediation.from_dict(sample_remediation.to_dict())
        assert result.summary == sample_remediation.summary
        assert len(result.steps) == 2
        assert len(result.citations) == 1
        assert result.citations[0].source == "Test Source"

    def test_finding_round_trip(self, sample_finding):
        result = Finding.from_dict(sample_finding.to_dict())
        assert result.status == "pass"
        assert result.score == 85.0
        assert result.attribute.id == "test_attr"
        assert result.remediation is not None
        assert result.remediation.summary == "Fix the issue"

    def test_finding_without_remediation(self, sample_attribute):
        f = Finding(
            attribute=sample_attribute,
            status="pass",
            score=90.0,
            measured_value="90%",
            threshold=">80%",
            evidence=[],
            remediation=None,
            error_message=None,
        )
        result = Finding.from_dict(f.to_dict())
        assert result.remediation is None

    def test_finding_error_status(self, sample_attribute):
        f = Finding.error(sample_attribute, "Something went wrong")
        result = Finding.from_dict(f.to_dict())
        assert result.status == "error"
        assert result.error_message == "Something went wrong"

    def test_metadata_round_trip(self):
        m = AssessmentMetadata(
            agentready_version="2.31.1",
            research_version="1.0",
            assessment_timestamp="2026-03-26T12:00:00",
            assessment_timestamp_human="March 26, 2026 at 12:00 PM",
            executed_by="test@host",
            command="agentready assess .",
            working_directory="/tmp/test",
        )
        result = AssessmentMetadata.from_dict(m.to_dict())
        assert result.agentready_version == "2.31.1"
        assert result.executed_by == "test@host"

    def test_discovered_skill_round_trip(self, sample_citation):
        s = DiscoveredSkill(
            skill_id="test-skill",
            name="Test Skill",
            description="A test skill",
            confidence=90.0,
            source_attribute_id="test_attr",
            reusability_score=80.0,
            impact_score=70.0,
            pattern_summary="A pattern",
            code_examples=["example"],
            citations=[sample_citation],
        )
        result = DiscoveredSkill.from_dict(s.to_dict())
        assert result.skill_id == "test-skill"
        assert result.confidence == 90.0
        assert len(result.citations) == 1

    def test_repository_round_trip(self, git_repo):
        r = Repository(
            path=git_repo,
            name="test-repo",
            url="https://github.com/test/repo",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 10},
            total_files=15,
            total_lines=500,
        )
        result = Repository.from_dict(r.to_dict())
        assert result.name == "test-repo"
        assert result.branch == "main"
        assert result.languages == {"Python": 10}

    def test_repository_from_dict_skips_filesystem_validation(self):
        """from_dict should not validate the path exists on disk,
        so cached assessments remain readable after the repo is moved."""
        data = {
            "path": "/nonexistent/repo/path",
            "name": "gone-repo",
            "url": "https://github.com/test/gone",
            "branch": "main",
            "commit_hash": "abc123",
            "languages": {"Python": 5},
            "total_files": 10,
            "total_lines": 200,
        }
        result = Repository.from_dict(data)
        assert result.name == "gone-repo"
        assert str(result.path) == "/nonexistent/repo/path"

    def test_remediation_from_dict_missing_steps_uses_summary(self):
        """If steps is missing or empty, from_dict should fall back to
        using the summary as a single step to satisfy the invariant."""
        data = {
            "summary": "Fix the issue",
            "tools": [],
            "commands": [],
            "examples": [],
            "citations": [],
        }
        result = Remediation.from_dict(data)
        assert result.steps == ["Fix the issue"]

    def test_assessment_round_trip(self, sample_assessment):
        data = sample_assessment.to_dict()
        result = Assessment.from_dict(data)
        assert result.overall_score == 85.0
        assert result.certification_level == "Gold"
        assert result.attributes_assessed == 1
        assert result.attributes_not_assessed == 0
        assert len(result.findings) == 1
        assert result.findings[0].score == 85.0

    def test_assessment_attributes_skipped_key_mapping(self, sample_assessment):
        """Verify that 'attributes_skipped' in serialized JSON maps to
        'attributes_not_assessed' in the model (the key mapping bug)."""
        data = sample_assessment.to_dict()
        # to_dict() serializes as 'attributes_skipped'
        assert "attributes_skipped" in data
        assert "attributes_not_assessed" not in data
        # from_dict() should correctly map it back
        result = Assessment.from_dict(data)
        assert result.attributes_not_assessed == 0


class TestCacheRoundTrip:
    """Test full cache set/get round-trip — the core regression test."""

    def test_cache_set_and_get(self, sample_assessment):
        """Regression test: cache.get() must return an Assessment, not raise
        NotImplementedError or return None."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))
            url = "https://github.com/test/repo"
            commit = "abc123"

            assert cache.set(url, commit, sample_assessment)
            result = cache.get(url, commit)

            assert result is not None
            assert isinstance(result, Assessment)
            assert result.overall_score == sample_assessment.overall_score
            assert result.certification_level == sample_assessment.certification_level
            assert len(result.findings) == len(sample_assessment.findings)

    def test_cache_miss_returns_none(self):
        """Cache miss should return None, not raise."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))
            result = cache.get("https://github.com/test/repo", "nonexistent")
            assert result is None

    def test_cache_preserves_finding_details(self, sample_assessment):
        """Ensure nested model data survives the cache round-trip."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))
            url = "https://github.com/test/repo"
            commit = "abc123"

            cache.set(url, commit, sample_assessment)
            result = cache.get(url, commit)

            finding = result.findings[0]
            assert finding.attribute.id == "test_attr"
            assert finding.attribute.tier == 1
            assert finding.remediation is not None
            assert finding.remediation.summary == "Fix the issue"
            assert len(finding.remediation.citations) == 1

    def test_cache_invalidate_then_miss(self, sample_assessment):
        """After invalidation, get should return None."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))
            url = "https://github.com/test/repo"
            commit = "abc123"

            cache.set(url, commit, sample_assessment)
            cache.invalidate(url, commit)
            assert cache.get(url, commit) is None

    def test_cache_expired_entry_returns_none(self, sample_assessment):
        """Expired entries should be deleted and return None."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir), ttl_days=0)

            url = "https://github.com/test/repo"
            commit = "abc123"

            # Manually insert with an already-expired timestamp
            assessment_json = json.dumps(sample_assessment.to_dict())
            expired = (datetime.now() - timedelta(hours=1)).isoformat()

            with sqlite3.connect(cache.db_path) as conn:
                conn.execute(
                    """INSERT INTO assessments
                    (repository_url, commit_hash, overall_score, assessment_json, expires_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (url, commit, 85.0, assessment_json, expired),
                )
                conn.commit()

            result = cache.get(url, commit)
            assert result is None

    def test_cache_malformed_json_returns_none(self):
        """Malformed cache entries should return None, not crash."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))
            url = "https://github.com/test/repo"
            commit = "abc123"

            # Insert malformed JSON missing required keys
            malformed = json.dumps({"overall_score": 50.0})
            expires = (datetime.now() + timedelta(days=7)).isoformat()

            with sqlite3.connect(cache.db_path) as conn:
                conn.execute(
                    """INSERT INTO assessments
                    (repository_url, commit_hash, overall_score, assessment_json, expires_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (url, commit, 50.0, malformed, expires),
                )
                conn.commit()

            result = cache.get(url, commit)
            assert result is None
