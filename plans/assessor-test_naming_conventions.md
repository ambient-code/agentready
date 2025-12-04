# feat: Implement TestNamingConventionsAssessor

## Attribute Definition

**Attribute ID**: `test_naming_conventions` (Attribute #22 - Tier 3)

**Definition**: Descriptive test names following patterns like `test_should_<expected>_when_<condition>`.

**Why It Matters**: Clear test names help AI understand intent without reading implementation. When tests fail, AI diagnoses issues faster with self-documenting names.

**Impact on Agent Behavior**:
- Generation of similar test patterns
- Faster edge case understanding
- More accurate fix proposals aligned with intent
- Better test coverage gap identification

**Measurable Criteria**:
- Pattern: `test_<method>_<scenario>_<expected_outcome>`
- Example: `test_create_user_with_invalid_email_raises_value_error`
- Avoid: `test1`, `test2`, `test_edge_case`, `test_bug_fix`, `test_method_name`
- Test names should be readable as sentences

## Implementation Requirements

**File Location**: `src/agentready/assessors/testing.py`

**Class Name**: `TestNamingConventionsAssessor`

**Tier**: 3 (Important)

**Default Weight**: 0.015 (1.5% of total score)

## Assessment Logic

**Scoring Approach**: Parse test files and analyze test function names

**Evidence to Check** (score components):
1. Descriptive test names (70%)
   - Count tests with descriptive names (>4 words, includes context)
   - Pattern: test_<action>_<condition>_<outcome>
   - Example: `test_login_with_invalid_password_returns_401`

2. Avoid anti-patterns (30%)
   - Generic names: test1, test2, test_edge_case
   - Just method name: test_create_user (no context)
   - Bug IDs: test_bug_123, test_issue_456

**Scoring Logic**:
```python
descriptive_tests = count_descriptive_test_names(test_functions)
total_tests = len(test_functions)

if total_tests == 0:
    return not_applicable

descriptive_percent = (descriptive_tests / total_tests) * 100

score = self.calculate_proportional_score(
    measured_value=descriptive_percent,
    threshold=80.0,
    higher_is_better=True,
)

status = "pass" if score >= 75 else "fail"
```

**Heuristic for Descriptive Names**:
- Name has 4+ words (split by underscores)
- Contains context words: with, when, if, given, should
- Contains outcome words: returns, raises, creates, updates, deletes
- NOT just: test_<function_name>

## Code Pattern to Follow

**Reference**: `TestCoverageAssessor` for test file detection

**Pattern**:
1. Find test files (test_*.py, *_test.py, *_spec.js)
2. Parse with AST to extract test function names
3. Analyze each test name for descriptiveness
4. Calculate percentage of well-named tests
5. Provide examples of good/bad names in evidence

## Example Finding Responses

### Pass (Score: 92)
```python
Finding(
    attribute=self.attribute,
    status="pass",
    score=92.0,
    measured_value="92%",
    threshold="≥80%",
    evidence=[
        "Descriptive test names: 46/50 tests",
        "Coverage: 92%",
        "Good examples:",
        "  - test_create_user_with_valid_data_returns_user_instance",
        "  - test_login_with_invalid_password_returns_401",
        "  - test_delete_user_with_nonexistent_id_raises_not_found",
    ],
    remediation=None,
    error_message=None,
)
```

### Fail (Score: 38)
```python
Finding(
    attribute=self.attribute,
    status="fail",
    score=38.0,
    measured_value="38%",
    threshold="≥80%",
    evidence=[
        "Descriptive test names: 19/50 tests",
        "Coverage: 38%",
        "Anti-patterns detected:",
        "  - test1, test2, test3 (generic numbering)",
        "  - test_create_user (no context or outcome)",
        "  - test_bug_123 (references bug ID, not behavior)",
        "  - test_edge_case (vague, no specifics)",
    ],
    remediation=self._create_remediation(),
    error_message=None,
)
```

### Not Applicable
```python
Finding.not_applicable(
    self.attribute,
    reason="No test files found in repository"
)
```

## Registration

Add to `src/agentready/services/scanner.py` in `create_all_assessors()`:

```python
from ..assessors.testing import (
    TestCoverageAssessor,
    PreCommitHooksAssessor,
    TestNamingConventionsAssessor,  # Add this import
)

def create_all_assessors() -> List[BaseAssessor]:
    return [
        # ... existing assessors ...
        TestNamingConventionsAssessor(),  # Add this line
    ]
```

## Testing Guidance

**Test File**: `tests/unit/test_assessors_testing.py`

**Test Cases to Add**:
1. `test_naming_pass_descriptive`: Tests with good descriptive names (>80%)
2. `test_naming_fail_generic`: Tests with test1, test2, testMethod
3. `test_naming_partial_score`: Mixed quality (60% descriptive)
4. `test_naming_not_applicable`: No test files found
5. `test_naming_edge_cases`: Handle empty test files, malformed tests

**Note**: AgentReady's own tests use descriptive names, should score well (85+).

## Dependencies

**External Tools**: None (AST parsing)

**Python Standard Library**:
- `ast` for parsing Python test files
- `re` for pattern matching test names
- `pathlib.Path` for finding test files

## Remediation Steps

```python
def _create_remediation(self) -> Remediation:
    return Remediation(
        summary="Improve test naming to be more descriptive and self-documenting",
        steps=[
            "Follow pattern: test_<action>_<condition>_<expected_outcome>",
            "Include context: what's being tested, under what conditions",
            "Specify expected outcome: returns, raises, creates, etc.",
            "Avoid generic names: test1, test2, test_edge_case",
            "Make names readable as sentences",
            "Refactor existing tests with poor names",
        ],
        tools=[],
        commands=[
            "# Find tests with generic names",
            "grep -r 'def test[0-9]' tests/",
            "grep -r 'def test_[a-z]*(' tests/  # Just method name, no context",
        ],
        examples=[
            """# Python - Good test names
def test_create_user_with_valid_data_returns_user_instance():
    user = create_user(email="test@example.com", name="Test")
    assert isinstance(user, User)

def test_create_user_with_invalid_email_raises_value_error():
    with pytest.raises(ValueError, match="Invalid email"):
        create_user(email="not-an-email", name="Test")

def test_create_user_with_duplicate_email_raises_integrity_error():
    create_user(email="test@example.com", name="Test 1")
    with pytest.raises(IntegrityError):
        create_user(email="test@example.com", name="Test 2")

# Python - Bad test names
def test1():  # What does this test?
    user = create_user(email="test@example.com", name="Test")
    assert user

def test_create_user():  # What's the expected outcome?
    user = create_user(email="test@example.com", name="Test")
    assert user

def test_bug_456():  # References issue, not behavior
    # ...
""",
            """// JavaScript - Good test names
describe('UserService', () => {
  it('should create user with valid data and return user instance', () => {
    const user = createUser({email: 'test@example.com', name: 'Test'});
    expect(user).toBeInstanceOf(User);
  });

  it('should throw error when creating user with invalid email', () => {
    expect(() => {
      createUser({email: 'invalid', name: 'Test'});
    }).toThrow('Invalid email');
  });
});

// JavaScript - Bad test names
describe('UserService', () => {
  it('test1', () => {  // Generic
    // ...
  });

  it('creates user', () => {  // No condition or outcome specified
    // ...
  });
});
""",
        ],
        citations=[
            Citation(
                source="pytest",
                title="Good Practices for Test Naming",
                url="https://docs.pytest.org/en/stable/explanation/goodpractices.html",
                relevance="pytest best practices for test organization and naming",
            ),
            Citation(
                source="JUnit",
                title="Best Practices for Writing Tests",
                url="https://junit.org/junit5/docs/current/user-guide/",
                relevance="Test naming conventions for Java/JUnit",
            ),
        ],
    )
```

## Implementation Notes

1. **Test File Detection**: Look for test_*.py, *_test.py, spec/*.js, __tests__/*.js
2. **AST Parsing**: Extract function names starting with `test_` or wrapped in `it()`/`test()`
3. **Descriptiveness Heuristic**:
   - Split name by underscores
   - Count words (4+ is good)
   - Check for context/outcome keywords
4. **Anti-Pattern Detection**:
   - Regex: `r'^test\d+$'` (test1, test2)
   - Regex: `r'^test_bug_\d+$'` (test_bug_123)
   - Just method name: `r'^test_[a-z_]+$'` with <4 words
5. **Scoring**: Proportional based on percentage of descriptive tests
6. **Edge Cases**: Empty test files, non-standard test frameworks
