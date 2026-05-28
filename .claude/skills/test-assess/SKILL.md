---
description: >
  Test agentready assess against real GitHub repositories to validate assessor
  changes. Selects repos relevant to the change being tested, clones them to a
  temp directory, runs the local checkout's assessor, reports results and output
  locations, then cleans up. Use when testing a new or modified assessor, verifying
  a PR's scoring behavior, or validating that a change works on real-world repos.
argument-hint: "[description of what to test]"
allowed-tools:
  - Bash(mktemp -d /tmp/agentready-test-*)
  - Bash(git clone *)
  - Bash(gh *)
  - Bash(yes *)
  - Bash(rm -rf /tmp/agentready-test-*)
  - Bash(PYTHONPATH=src python -m agentready *)
---

# Test agentready assess on real repositories

You are testing the agentready assessment tool against real GitHub repositories
to validate that a change works correctly.

### 1. Determine what to test

The user will describe what assessor behavior they want to validate (e.g., "test
Husky detection", "verify the new CI gates assessor"). If the description is
unclear, ask a brief clarifying question.

### 2. Ensure the code under test is checked out

Check which branch is currently active. If the change being tested is on a
different branch or PR, check it out first. If it is a PR, use
`gh pr checkout <number>`.

### 3. Select repositories

Search GitHub for repositories that are relevant to the feature being tested.
For example, if testing Husky hook detection, find repos that use Husky.

**How many repos:**
- Small or targeted changes: at least 1 repo
- Larger or riskier changes: 3 to 5 repos

**Selection criteria (in priority order):**
1. **Relevance**: repos must exercise the specific behavior being tested.
   This is the most important criterion.
2. **Variety of maturity**: when possible, mix large popular projects with
   smaller or newer ones. But never sacrifice relevance for variety.

Use `gh search repos`, `gh api`, or `gh search code` to find candidates.
Briefly confirm your repo selections with the user before cloning.

### 4. Clone repos to a temp directory

Create a unique temp directory for this test run:

```bash
TESTDIR=$(mktemp -d /tmp/agentready-test-XXXXXX)
```

Shallow clone each repo into that directory:

```bash
git clone --depth 1 <repo-url> $TESTDIR/<repo-name>
```

### 5. Run assessments

Run each assessment using the local checkout, not the globally installed package:

```bash
yes | PYTHONPATH=src python -m agentready assess $TESTDIR/<repo-name>
```

The `yes |` prefix auto-confirms the large-repo prompt if it appears.

### 6. Report results

After each assessment completes, report to the user:
- The repo name and the overall score/certification level
- The specific finding(s) relevant to what is being tested, including
  status, score, and evidence
- The exact paths to the JSON, HTML, and Markdown reports so the user can
  inspect them

Summarize all results in a table at the end if multiple repos were tested.

### 7. Clean up

After the user has seen the results, delete the temp directory:

```bash
rm -rf $TESTDIR
```

Tell the user the cleanup is done. If any repo's reports are worth preserving,
ask before deleting.
