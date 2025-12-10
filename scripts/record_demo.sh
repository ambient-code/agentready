#!/bin/bash
# Terminal demo recording script for AgentReady eval harness
#
# This script records an interactive terminal session demonstrating
# the complete eval harness workflow using asciinema.
#
# Prerequisites:
#   - asciinema installed (brew install asciinema / apt install asciinema)
#   - AgentReady installed in development mode
#   - Virtual environment activated
#
# Usage:
#   ./scripts/record_demo.sh
#   ./scripts/record_demo.sh --output docs/assets/recordings/custom.cast

set -e  # Exit on error

# Configuration
OUTPUT_FILE="${1:-docs/assets/recordings/eval-harness.cast}"
REPO_PATH="$(pwd)"
COLS=120
ROWS=30
TITLE="AgentReady Eval Harness Demo"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎬 AgentReady Terminal Demo Recording${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "Output file: $OUTPUT_FILE"
echo "Repo path: $REPO_PATH"
echo "Dimensions: ${COLS}x${ROWS}"
echo ""

# Check prerequisites
if ! command -v asciinema &> /dev/null; then
    echo "❌ asciinema not found. Install with:"
    echo "   brew install asciinema  (macOS)"
    echo "   apt install asciinema   (Ubuntu/Debian)"
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run: uv venv"
    exit 1
fi

# Create output directory
mkdir -p "$(dirname "$OUTPUT_FILE")"

echo -e "${GREEN}✅ Prerequisites met${NC}"
echo ""
echo "Recording will demonstrate:"
echo "  1. agentready eval-harness baseline"
echo "  2. agentready eval-harness test-assessor"
echo "  3. agentready eval-harness summarize"
echo "  4. agentready eval-harness dashboard"
echo ""
echo "Press ENTER to start recording (Ctrl+D to stop)..."
read

# Recording script content
cat > /tmp/agentready_demo_script.sh << 'EOF'
#!/bin/bash
# Automated demo script executed within asciinema

# Setup
cd "${AGENTREADY_REPO}"
source .venv/bin/activate

# Clear screen
clear

# Title
echo "🚀 AgentReady Eval Harness Demo"
echo "=================================="
echo ""
sleep 2

# Command 1: Baseline
echo "$ agentready eval-harness baseline . --iterations 3 --verbose"
sleep 1
agentready eval-harness baseline . --iterations 3 --verbose
sleep 3
echo ""

# Command 2: Test Assessor
echo "$ agentready eval-harness test-assessor --assessor-id claude_md_file --iterations 3 --verbose"
sleep 1
agentready eval-harness test-assessor --assessor-id claude_md_file --iterations 3 --verbose
sleep 3
echo ""

# Command 3: Summarize
echo "$ agentready eval-harness summarize --verbose"
sleep 1
agentready eval-harness summarize --verbose
sleep 3
echo ""

# Command 4: Dashboard
echo "$ agentready eval-harness dashboard --verbose"
sleep 1
agentready eval-harness dashboard --verbose
sleep 3
echo ""

# Final message
echo "✅ Demo complete!"
echo ""
echo "View results:"
echo "  • Dashboard: docs/_data/tbench/"
echo "  • Raw data: .agentready/eval_harness/"
echo ""
sleep 2

# Exit
exit 0
EOF

chmod +x /tmp/agentready_demo_script.sh

# Start recording
echo -e "${GREEN}🎥 Recording started...${NC}"
echo ""

AGENTREADY_REPO="$REPO_PATH" asciinema rec "$OUTPUT_FILE" \
  --title "$TITLE" \
  --cols "$COLS" \
  --rows "$ROWS" \
  --command "/tmp/agentready_demo_script.sh"

# Cleanup
rm -f /tmp/agentready_demo_script.sh

# Success
echo ""
echo -e "${GREEN}✅ Recording saved to: $OUTPUT_FILE${NC}"
echo ""
echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
echo "Next steps:"
echo "  1. Review recording:"
echo "     asciinema play $OUTPUT_FILE"
echo ""
echo "  2. Upload to asciinema.org (optional):"
echo "     asciinema upload $OUTPUT_FILE"
echo ""
echo "  3. Embed in docs/demos/terminal-demo.html"
echo ""
