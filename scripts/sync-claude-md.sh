#!/bin/bash
# Sync CLAUDE.md with current project metrics
# Used by semantic-release during the release process

set -e

VERSION=${1:-$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')}
TODAY=$(date +%Y-%m-%d)

echo "Syncing CLAUDE.md to version $VERSION (date: $TODAY)"

# Update all version numbers (simpler regex that works across different sed versions)
sed -i.bak "s/v[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/v$VERSION/g" CLAUDE.md
sed -i.bak "s/\*\*AgentReady Version\*\*: [0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/\*\*AgentReady Version\*\*: $VERSION/" CLAUDE.md

# Update "Last Updated" date at top (first occurrence only)
awk -v today="$TODAY" '
  !updated && /\*\*Last Updated\*\*:/ {
    sub(/[0-9]{4}-[0-9]{2}-[0-9]{2}/, today);
    updated=1
  }
  {print}
' CLAUDE.md > CLAUDE.md.tmp && mv CLAUDE.md.tmp CLAUDE.md

# Update "Last Updated" date at bottom (second occurrence)
awk -v today="$TODAY" '
  /\*\*Last Updated\*\*:.*by Jeremy Eder/ {
    sub(/[0-9]{4}-[0-9]{2}-[0-9]{2}/, today);
  }
  {print}
' CLAUDE.md > CLAUDE.md.tmp && mv CLAUDE.md.tmp CLAUDE.md

# Try to extract self-assessment score (if examples exist)
if [ -f "examples/self-assessment/assessment-latest.json" ]; then
  SCORE=$(python3 -c "
import json
try:
    with open('examples/self-assessment/assessment-latest.json') as f:
        data = json.load(f)
        print(f\"{data['overall_score']}\")
except Exception as e:
    print('unknown', file=sys.stderr)
    exit(1)
" 2>/dev/null || echo "")

  if [ -n "$SCORE" ] && [ "$SCORE" != "unknown" ]; then
    echo "Updating self-assessment score to $SCORE"
    # Update self-assessment scores (match any number with optional decimal)
    sed -i.bak "s/[0-9][0-9]*\.[0-9][0-9]*\/100/$SCORE\/100/g" CLAUDE.md
  fi
fi

# Clean up backup files
rm -f CLAUDE.md.bak

echo "✓ CLAUDE.md synced successfully"
echo "  - Version: $VERSION"
echo "  - Date: $TODAY"
if [ -n "$SCORE" ]; then
  echo "  - Self-Assessment: $SCORE/100"
fi
