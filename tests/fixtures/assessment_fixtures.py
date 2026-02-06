"""Shared test fixtures for creating valid Assessment JSON data.

This module provides factory functions for generating valid Assessment and Finding
JSON structures that match the current schema (v1.0.0).

The fixtures ensure consistency across tests and prevent schema breakage.
"""


def create_test_assessment_json(
    overall_score=85.0,
    num_findings=2,
    repo_path="/tmp/test",
    repo_name="test-repo",
    certification_level=None,
):
    """Create valid Assessment JSON matching current schema.

    Args:
        overall_score: Score between 0-100
        num_findings: Number of findings to include (must match attributes_total)
        repo_path: Repository path
        repo_name: Repository name
        certification_level: Override certification level (auto-calculated if None)

    Returns:
        dict: Valid Assessment JSON that can be serialized and loaded
    """
    if certification_level is None:
        # Auto-calculate certification level
        if overall_score >= 90:
            certification_level = "Platinum"
        elif overall_score >= 75:
            certification_level = "Gold"
        elif overall_score >= 60:
            certification_level = "Silver"
        elif overall_score >= 40:
            certification_level = "Bronze"
        else:
            certification_level = "Needs Improvement"

    findings = []
    for i in range(num_findings):
        status = "pass" if overall_score >= 60 else "fail"
        score = overall_score if status == "pass" else max(0, overall_score - 10)
        findings.append(
            create_test_finding_json(
                attribute_id=f"test_attr_{i}",
                attribute_name=f"Test Attribute {i}",
                status=status,
                score=score,
            )
        )

    return {
        "schema_version": "1.0.0",
        "timestamp": "2025-11-22T06:00:00",
        "repository": {
            "name": repo_name,
            "path": repo_path,
            "url": None,
            "branch": "main",
            "commit_hash": "abc123",
            "languages": {"Python": 100},
            "total_files": 10,
            "total_lines": 500,
        },
        "overall_score": overall_score,
        "certification_level": certification_level,
        "attributes_assessed": num_findings,
        "attributes_skipped": 0,
        "attributes_total": num_findings,
        "findings": findings,
        "config": None,  # CRITICAL: Must be present in current schema
        "duration_seconds": 1.5,
        "discovered_skills": [],  # Optional but good to include
    }


def create_test_finding_json(
    attribute_id="test_attr",
    attribute_name="Test Attribute",
    status="pass",
    score=90.0,
    category="Documentation",
    tier=1,
):
    """Create valid Finding JSON.

    Args:
        attribute_id: Unique attribute identifier
        attribute_name: Human-readable attribute name
        status: pass, fail, skipped, error, or not_applicable
        score: Score 0-100 (or None for non-pass/fail statuses)
        category: Attribute category
        tier: Attribute tier (1-4)

    Returns:
        dict: Valid Finding JSON
    """
    return {
        "attribute": {
            "id": attribute_id,
            "name": attribute_name,
            "category": category,
            "tier": tier,
            "description": f"Test description for {attribute_name}",
            "criteria": "Test criteria",
            "default_weight": 1.0,
        },
        "status": status,
        "score": score if status in ("pass", "fail") else None,
        "measured_value": "present" if status == "pass" else "missing",
        "threshold": "present",
        "evidence": [f"Test evidence for {attribute_name}"],
        "error_message": None if status != "error" else "Test error",
    }


def create_test_repository_json(path="/tmp/test", name="test-repo", languages=None):
    """Create valid Repository JSON.

    Args:
        path: Repository path
        name: Repository name
        languages: Language breakdown dict (default: {"Python": 100})

    Returns:
        dict: Valid Repository JSON
    """
    if languages is None:
        languages = {"Python": 100}

    return {
        "name": name,
        "path": path,
        "url": None,
        "branch": "main",
        "commit_hash": "abc123",
        "languages": languages,
        "total_files": 10,
        "total_lines": 500,
    }
