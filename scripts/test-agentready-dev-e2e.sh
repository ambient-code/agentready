#!/bin/bash
# End-to-end test script for agentready-dev workflow
#
# This script:
# 1. Creates a new test issue with @agentready-dev mention
# 2. Waits for the workflow to trigger and complete
# 3. Verifies the workflow posted a comment back
# 4. Reports success/failure
#
# Usage:
#   ./scripts/test-agentready-dev-e2e.sh
#   Or with explicit token:
#   GITHUB_TOKEN=<token> ./scripts/test-agentready-dev-e2e.sh

set -euo pipefail

OWNER="ambient-code"
REPO="agentready"
TIMESTAMP=$(date +%s)
TEST_ISSUE_TITLE="[TEST] E2E Test for @agentready-dev workflow - $TIMESTAMP"
TEST_ISSUE_BODY=$(cat <<EOF
This is an automated end-to-end test for the @agentready-dev workflow.

**Test Details:**
- Created: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
- Test ID: $TIMESTAMP

@agentready-dev Please analyze this test issue and post your response as a comment.

**Expected Behavior:**
1. Workflow should trigger on issue creation
2. Claude Code Action should analyze the request
3. A comment should be posted back indicating the @agentready-dev agent responded

This issue will be automatically closed after the test completes.
EOF
)

echo "🧪 Starting E2E test for @agentready-dev workflow..."
echo ""

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
  echo "❌ Error: GitHub CLI (gh) must be installed"
  echo "   Install: https://cli.github.com/"
  exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
  echo "❌ Error: Not authenticated with GitHub CLI"
  echo "   Run: gh auth login"
  exit 1
fi

echo "✅ GitHub CLI authenticated"
echo ""

# Step 1: Create test issue
echo "1️⃣  Creating test issue..."
ISSUE_RESULT=$(gh api "repos/${OWNER}/${REPO}/issues" \
  -X POST \
  -f title="$TEST_ISSUE_TITLE" \
  -f body="$TEST_ISSUE_BODY" 2>&1)

if [ $? -ne 0 ]; then
  echo "   ❌ Error creating issue: $ISSUE_RESULT"
  exit 1
fi

ISSUE_NUMBER=$(echo "$ISSUE_RESULT" | jq -r '.number')
ISSUE_URL=$(echo "$ISSUE_RESULT" | jq -r '.html_url')

if [ -z "$ISSUE_NUMBER" ] || [ "$ISSUE_NUMBER" = "null" ]; then
  echo "   ❌ Failed to extract issue number from response"
  echo "   Response: $ISSUE_RESULT"
  exit 1
fi

echo "   ✅ Created issue #${ISSUE_NUMBER}"
echo "   📝 Issue URL: $ISSUE_URL"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 TEST ISSUE NUMBER: #${ISSUE_NUMBER}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 2: Wait for workflow to trigger
echo "2️⃣  Waiting for workflow to trigger (checking every 5 seconds)..."
ISSUE_CREATED_AT=$(gh api "repos/${OWNER}/${REPO}/issues/${ISSUE_NUMBER}" --jq '.created_at')
echo "   Issue created at: $ISSUE_CREATED_AT"

MAX_WAIT=120  # 2 minutes max wait
ELAPSED=0
WORKFLOW_FOUND=false
WORKFLOW_RUN_ID=""

while [ $ELAPSED -lt $MAX_WAIT ]; do
  # Get the most recent workflow run
  LATEST_RUN=$(gh run list --workflow=agentready-dev.yml --limit 1 --json databaseId,status,conclusion,createdAt --jq '.[0]' 2>&1)

  if [ $? -eq 0 ] && [ "$LATEST_RUN" != "null" ] && [ -n "$LATEST_RUN" ]; then
    RUN_ID=$(echo "$LATEST_RUN" | jq -r '.databaseId')
    RUN_STATUS=$(echo "$LATEST_RUN" | jq -r '.status')
    RUN_CONCLUSION=$(echo "$LATEST_RUN" | jq -r '.conclusion // "pending"')
    RUN_CREATED=$(echo "$LATEST_RUN" | jq -r '.createdAt')

    # Check if this run was created after the issue (within 2 minutes)
    if [ -n "$RUN_ID" ] && [ "$RUN_ID" != "null" ]; then
      # Simple check: if run was created recently (within last 3 minutes), assume it's ours
      WORKFLOW_FOUND=true
      WORKFLOW_RUN_ID=$RUN_ID
      echo "   ✅ Found workflow run #${RUN_ID}"
      echo "   Created: $RUN_CREATED"
      echo "   Status: $RUN_STATUS"
      echo "   Conclusion: $RUN_CONCLUSION"
      break
    fi
  fi

  echo "   ⏳ Waiting... (${ELAPSED}s elapsed)"
  sleep 5
  ELAPSED=$((ELAPSED + 5))
done

if [ "$WORKFLOW_FOUND" = false ]; then
  echo "   ⚠️  Workflow not found within ${MAX_WAIT} seconds"
  echo "   This might be okay if the workflow takes longer to trigger"
fi

echo ""

# Step 3: Wait for workflow to complete
if [ "$WORKFLOW_FOUND" = true ]; then
  echo "3️⃣  Waiting for workflow to complete..."
  MAX_COMPLETE_WAIT=300  # 5 minutes max wait
  ELAPSED=0
  WORKFLOW_COMPLETE=false

  while [ $ELAPSED -lt $MAX_COMPLETE_WAIT ]; do
    RUN_INFO=$(gh api "repos/${OWNER}/${REPO}/actions/runs/${WORKFLOW_RUN_ID}" 2>&1)
    STATUS=$(echo "$RUN_INFO" | jq -r '.status')
    CONCLUSION=$(echo "$RUN_INFO" | jq -r '.conclusion // "pending"')

    if [ "$STATUS" = "completed" ]; then
      WORKFLOW_COMPLETE=true
      echo "   ✅ Workflow completed"
      echo "   Conclusion: $CONCLUSION"
      break
    fi

    echo "   ⏳ Status: $STATUS, Conclusion: $CONCLUSION (${ELAPSED}s elapsed)"
    sleep 10
    ELAPSED=$((ELAPSED + 10))
  done

  if [ "$WORKFLOW_COMPLETE" = false ]; then
    echo "   ⚠️  Workflow did not complete within ${MAX_COMPLETE_WAIT} seconds"
  fi

  echo ""
fi

# Step 4: Wait a bit more for comment to be posted
echo "4️⃣  Waiting for comment to be posted (10 seconds)..."
sleep 10
echo ""

# Step 5: Check for comments
echo "5️⃣  Checking for comments on issue #${ISSUE_NUMBER}..."
COMMENTS=$(gh api "repos/${OWNER}/${REPO}/issues/${ISSUE_NUMBER}/comments" 2>&1)
COMMENT_COUNT=$(echo "$COMMENTS" | jq '. | length')

echo "   Found $COMMENT_COUNT total comments"

# Look for comments from github-actions[bot] or containing @agentready-dev
AGENTREADY_COMMENTS=$(echo "$COMMENTS" | jq '[.[] | select(
  (.user.login == "github-actions[bot]") or
  (.body | contains("@agentready-dev")) or
  (.body | contains("agentready-dev"))
)]')

AGENTREADY_COUNT=$(echo "$AGENTREADY_COMMENTS" | jq '. | length')
echo "   Found $AGENTREADY_COUNT comments from workflow or mentioning @agentready-dev"

if [ "$AGENTREADY_COUNT" -gt 0 ]; then
  echo ""
  echo "   ✅ SUCCESS! Found comment(s) from workflow:"
  echo ""

  # Show each comment
  echo "$AGENTREADY_COMMENTS" | jq -r '.[] | "
   ┌─────────────────────────────────────────────────────────────
   │ Comment by: \(.user.login)
   │ Posted: \(.created_at)
   │ URL: \(.html_url)
   │
   │ \(.body | split("\n")[0:5] | join("\n"))
   │ \(if (.body | split("\n") | length) > 5 then "   ... (truncated)" else "" end)
   └─────────────────────────────────────────────────────────────
   "'

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "✅ E2E TEST PASSED!"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "📋 Test Issue: #${ISSUE_NUMBER}"
  echo "🔗 Issue URL: $ISSUE_URL"
  if [ "$WORKFLOW_FOUND" = true ]; then
    echo "🔗 Workflow Run: https://github.com/${OWNER}/${REPO}/actions/runs/${WORKFLOW_RUN_ID}"
  fi
  echo ""

  # Optionally close the issue
  read -p "Close test issue #${ISSUE_NUMBER}? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    gh issue close "$ISSUE_NUMBER" --comment "✅ E2E test completed successfully. Closing test issue."
    echo "✅ Issue closed"
  fi

  exit 0
else
  echo ""
  echo "   ❌ FAILURE! No comment found from workflow"
  echo ""

  # Show recent comments for debugging
  if [ "$COMMENT_COUNT" -gt 0 ]; then
    echo "   Recent comments:"
    echo "$COMMENTS" | jq -r '.[-3:] | reverse | .[] | "   - [\(.user.login)] \(.body | split("\n")[0] | .[0:60])..."'
  fi

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "❌ E2E TEST FAILED"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "📋 Test Issue: #${ISSUE_NUMBER}"
  echo "🔗 Issue URL: $ISSUE_URL"
  if [ "$WORKFLOW_FOUND" = true ]; then
    echo "🔗 Workflow Run: https://github.com/${OWNER}/${REPO}/actions/runs/${WORKFLOW_RUN_ID}"
    echo ""
    echo "🔍 Debugging steps:"
    echo "   1. Check workflow logs: https://github.com/${OWNER}/${REPO}/actions/runs/${WORKFLOW_RUN_ID}"
    echo "   2. Check 'Debug event context' step output"
    echo "   3. Check 'Post @agentready-dev response' step output"
    echo "   4. Verify issue number extraction"
  else
    echo ""
    echo "⚠️  Workflow did not trigger. Check:"
    echo "   1. Workflow file is on main branch"
    echo "   2. Workflow is enabled in repository settings"
    echo "   3. Issue contains @agentready-dev mention"
  fi
  echo ""

  exit 1
fi
