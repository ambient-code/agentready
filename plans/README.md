# AgentReady Assessor Implementation Plans

This directory contains cold-start prompts for implementing 13 new assessors in the AgentReady project. Each file is a self-contained specification ready to be used as a GitHub issue body or development guide.

## Overview

**Total Assessors**: 13 (expanding AgentReady from 10/25 to 23/25 attributes implemented)

**Tier Distribution**:
- **Tier 2 (Critical)**: 5 assessors (3% weight each)
- **Tier 3 (Important)**: 7 assessors (1.5% weight each)
- **Tier 4 (Advanced)**: 1 assessor (0.5% weight)

**Estimated Impact**: Increases AgentReady self-assessment score from ~75.4 (Gold) to ~85+ (Platinum potential)

---

## Tier 2 (Critical) - 3% Weight Each

### 1. OneCommandSetupAssessor
**File**: `assessor-one_command_setup.md`
**Attribute ID**: `one_command_setup` (#12)
**Location**: `structure.py`
**Complexity**: Medium
**Dependencies**: None (file system + README parsing)

Single command to set up development environment from fresh clone. Checks for Makefile, setup scripts, README documentation.

### 2. ConciseDocumentationAssessor
**File**: `assessor-concise_documentation.md`
**Attribute ID**: `concise_documentation` (#13)
**Location**: `documentation.py`
**Complexity**: Medium
**Dependencies**: None (Markdown parsing)

Documentation maximizing information density while minimizing token consumption. Analyzes README length, heading structure, bullet points vs prose.

### 3. InlineDocumentationAssessor
**File**: `assessor-inline_documentation.md`
**Attribute ID**: `inline_documentation` (#14)
**Location**: `documentation.py`
**Complexity**: High
**Dependencies**: AST parsing (similar to TypeAnnotationsAssessor)

Function, class, and module-level docstrings (Python PEP 257, JSDoc/TSDoc). Uses AST to count functions with docstrings.

### 4. SeparationOfConcernsAssessor
**File**: `assessor-separation_of_concerns.md`
**Attribute ID**: `separation_of_concerns` (#17)
**Location**: `structure.py`
**Complexity**: High
**Dependencies**: AST parsing for import analysis

Organizing code so each module/file/function has single responsibility. Detects layer-based vs feature-based organization, circular dependencies.

### 5. GitignoreCompletenessAssessor
**File**: `assessor-gitignore_completeness.md`
**Attribute ID**: `gitignore_completeness` (#16)
**Location**: `structure.py`
**Complexity**: Low
**Dependencies**: None (file reading)

Comprehensive .gitignore preventing sensitive files, build artifacts, and environment-specific files from version control.

---

## Tier 3 (Important) - 1.5% Weight Each

### 6. StructuredLoggingAssessor
**File**: `assessor-structured_logging.md`
**Attribute ID**: `structured_logging` (#18)
**Location**: `code_quality.py`
**Complexity**: Medium
**Dependencies**: Dependency file parsing

Logging in structured format (JSON) with consistent field names. Checks for structlog, winston, zap in dependencies.

### 7. OpenAPISpecsAssessor
**File**: `assessor-openapi_specs.md`
**Attribute ID**: `openapi_specs` (#19)
**Location**: `documentation.py`
**Complexity**: Medium
**Dependencies**: YAML/JSON parsing

Machine-readable API documentation in OpenAPI format. Checks for openapi.yaml, validates version and completeness.

### 8. ArchitectureDecisionsAssessor
**File**: `assessor-architecture_decisions.md`
**Attribute ID**: `architecture_decisions` (#20)
**Location**: `documentation.py`
**Complexity**: Low
**Dependencies**: None (file system + Markdown parsing)

Architecture Decision Records (ADRs) documenting major design choices. Checks for docs/adr/ directory, validates ADR template compliance.

### 9. SemanticNamingAssessor
**File**: `assessor-semantic_naming.md`
**Attribute ID**: `semantic_naming` (#21)
**Location**: `code_quality.py`
**Complexity**: High
**Dependencies**: AST parsing

Systematic naming patterns following language conventions (PEP 8, camelCase, etc.). Detects anti-patterns like single-letter variables, abbreviations.

### 10. TestNamingConventionsAssessor
**File**: `assessor-test_naming_conventions.md`
**Attribute ID**: `test_naming_conventions` (#22)
**Location**: `testing.py`
**Complexity**: Medium
**Dependencies**: AST parsing for test functions

Descriptive test names following `test_<action>_<condition>_<outcome>` pattern. Avoids test1, test2, generic names.

### 11. IssuePRTemplatesAssessor
**File**: `assessor-issue_pr_templates.md`
**Attribute ID**: `issue_pr_templates` (#23)
**Location**: `structure.py`
**Complexity**: Low
**Dependencies**: None (file system)

Standardized templates for issues and PRs in .github/ directory. Checks for PULL_REQUEST_TEMPLATE.md and ISSUE_TEMPLATE/.

### 12. CICDPipelineVisibilityAssessor
**File**: `assessor-cicd_pipeline_visibility.md`
**Attribute ID**: `cicd_pipeline_visibility` (#24)
**Location**: `testing.py`
**Complexity**: Medium
**Dependencies**: YAML parsing

Clear, well-documented CI/CD configuration files. Checks for GitHub Actions, GitLab CI, CircleCI, etc. Validates job names, caching, parallelization.

### 13. BranchProtectionAssessor
**File**: `assessor-branch_protection.md`
**Attribute ID**: `branch_protection` (#25)
**Location**: `testing.py`
**Complexity**: High
**Dependencies**: GitHub API (gh CLI)

Required status checks and review approvals before merging. Uses GitHub API to query branch protection rules. **Note**: Requires GitHub integration.

---

## Tier 4 (Advanced) - 0.5% Weight

### 14. CodeSmellsAssessor
**File**: `assessor-code_smells.md`
**Attribute ID**: `code_smells` (#29)
**Location**: `code_quality.py`
**Complexity**: High
**Dependencies**: AST parsing, optional external tools

Removing indicators of deeper problems: long methods, large classes, duplicate code, magic numbers. Heuristic detection of common anti-patterns.

---

## Implementation Priority Recommendations

### Phase 1: Quick Wins (Low Complexity, High Impact)
1. ✅ **GitignoreCompletenessAssessor** - Easiest, immediate value
2. ✅ **IssuePRTemplatesAssessor** - Simple file checks
3. ✅ **ArchitectureDecisionsAssessor** - File system + basic validation
4. ✅ **OneCommandSetupAssessor** - README parsing + file checks

### Phase 2: Medium Complexity (Core Functionality)
5. ✅ **ConciseDocumentationAssessor** - Markdown analysis
6. ✅ **StructuredLoggingAssessor** - Dependency parsing
7. ✅ **OpenAPISpecsAssessor** - YAML/JSON parsing
8. ✅ **CICDPipelineVisibilityAssessor** - YAML parsing + validation
9. ✅ **TestNamingConventionsAssessor** - AST parsing

### Phase 3: Advanced AST Analysis
10. ✅ **InlineDocumentationAssessor** - AST docstring detection
11. ✅ **SemanticNamingAssessor** - AST identifier analysis
12. ✅ **SeparationOfConcernsAssessor** - AST import analysis
13. ✅ **CodeSmellsAssessor** - Multi-heuristic smell detection

### Phase 4: External Dependencies (Optional)
14. ⚠️ **BranchProtectionAssessor** - Requires GitHub API (may not work for all repos)

---

## Common Patterns Across Assessors

### File Locations
- **Documentation**: `src/agentready/assessors/documentation.py` (4 assessors)
- **Code Quality**: `src/agentready/assessors/code_quality.py` (4 assessors)
- **Structure**: `src/agentready/assessors/structure.py` (4 assessors)
- **Testing**: `src/agentready/assessors/testing.py` (4 assessors)

### Techniques
- **File System Checks**: 8 assessors (simple existence checks)
- **AST Parsing**: 6 assessors (Python/JS code analysis)
- **YAML/JSON Parsing**: 3 assessors (config file validation)
- **External API**: 1 assessor (GitHub API)

### Scoring Approaches
- **Binary (0 or 100)**: 3 assessors (file exists or not)
- **Proportional**: 9 assessors (percentage-based scoring)
- **Multi-Component**: 1 assessor (weighted sub-scores)

---

## Usage

### As GitHub Issues
Each file is formatted for direct use as a GitHub issue body:

```bash
# Create all issues at once
for file in .plans/assessor-*.md; do
  gh issue create --title "$(head -1 $file | sed 's/# //')" --body-file "$file"
done
```

### As Development Guide
Use files directly as implementation specifications:

```bash
# Read specification
cat .plans/assessor-one_command_setup.md

# Implement following the pattern
# Test using provided test cases
# Register in scanner.py
```

### For AI Agents
Cold-start prompts designed for AI-assisted implementation:

```
Please implement the OneCommandSetupAssessor following the specification in .plans/assessor-one_command_setup.md
```

---

## Testing Strategy

**Unit Tests**: Each assessor needs 3-5 unit tests
- Pass scenario (score ≥75)
- Fail scenario (score <75)
- Partial score scenario
- Not applicable scenario
- Edge cases

**Integration Tests**: Run full assessment on test repositories
- Minimal repo (few attributes)
- Well-structured repo (most attributes)
- AgentReady self-assessment

**Coverage Target**: >80% for new assessors

---

## Expected Outcomes

### Before (Current State)
- **Implemented**: 10/25 attributes (40%)
- **Self-Assessment**: 75.4/100 (Gold)
- **Tier 1**: 4/5 implemented (80%)
- **Tier 2**: 3/6 implemented (50%)
- **Tier 3**: 3/9 implemented (33%)
- **Tier 4**: 0/5 implemented (0%)

### After (With These 13 Assessors)
- **Implemented**: 23/25 attributes (92%)
- **Self-Assessment**: ~85-90/100 (Platinum potential)
- **Tier 1**: 4/5 implemented (80%) - unchanged
- **Tier 2**: 8/6 implemented (100%+) - fully covered
- **Tier 3**: 10/9 implemented (100%+) - fully covered
- **Tier 4**: 1/5 implemented (20%)

### Missing After Implementation (2 attributes)
- **Tier 1**: #3 - File Size Limits (not yet prioritized)
- **Tier 4**: 4 advanced attributes (dependency freshness, security scanning, performance benchmarks, etc.)

---

## Notes

1. **BranchProtectionAssessor** requires GitHub API access - may need to be optional or provide graceful degradation
2. All assessors follow existing patterns from `TypeAnnotationsAssessor`, `READMEAssessor`, etc.
3. Each prompt includes: attribute definition, implementation requirements, code patterns, examples, testing guidance, dependencies, and remediation steps
4. Prompts are self-contained - can be used independently or as a batch

---

**Last Updated**: 2025-11-22
**Created By**: Claude Code (Sonnet 4.5)
**Project**: AgentReady v1.0.0
