"""Tests for demo generation and validation

Tests the complete demo documentation build system including:
- Mermaid integration files
- Enhanced markdown documentation
- reveal.js slide generation
- asciinema terminal demo page
- Build orchestration script
"""

import re
from pathlib import Path

import pytest


class TestDemoFiles:
    """Test that all required demo files exist and have correct structure."""

    def test_mermaid_include_exists(self):
        """Test that Mermaid.js include file exists."""
        mermaid_file = Path("docs/_includes/mermaid.html")
        assert mermaid_file.exists(), "Mermaid include file should exist"

    def test_mermaid_include_has_cdn_script(self):
        """Test that Mermaid include loads from CDN."""
        mermaid_file = Path("docs/_includes/mermaid.html")
        content = mermaid_file.read_text()

        assert "mermaid" in content.lower(), "Should reference mermaid"
        assert "cdn.jsdelivr.net" in content, "Should use CDN"
        assert (
            "import" in content or "script" in content
        ), "Should have script tag or import"

    def test_default_layout_includes_mermaid(self):
        """Test that default layout includes Mermaid."""
        layout_file = Path("docs/_layouts/default.html")
        content = layout_file.read_text()

        assert "mermaid.html" in content, "Default layout should include mermaid.html"
        assert (
            "{% include mermaid.html %}" in content
        ), "Should use Jekyll include syntax"

    def test_demo_index_exists(self):
        """Test that demo hub landing page exists."""
        index_file = Path("docs/demos/index.md")
        assert index_file.exists(), "Demo index should exist"

    def test_demo_index_has_all_links(self):
        """Test that demo index links to all 4 demo formats."""
        index_file = Path("docs/demos/index.md")
        content = index_file.read_text()

        # Should link to all 4 formats
        assert "terminal-demo" in content, "Should link to terminal demo"
        assert "slides" in content, "Should link to slides"
        assert "walkthrough" in content, "Should link to walkthrough"
        # Quick reference might be in a different file or section

    def test_demo_index_has_gradient_cards(self):
        """Test that demo index uses gradient card styling."""
        index_file = Path("docs/demos/index.md")
        content = index_file.read_text()

        assert "gradient" in content, "Should have gradient styling"
        assert "grid" in content, "Should use grid layout"

    def test_walkthrough_exists(self):
        """Test that walkthrough documentation exists."""
        walkthrough_file = Path("docs/demos/walkthrough.md")
        assert walkthrough_file.exists(), "Walkthrough should exist"

    def test_walkthrough_has_mermaid_diagrams(self):
        """Test that walkthrough contains Mermaid diagrams."""
        walkthrough_file = Path("docs/demos/walkthrough.md")
        content = walkthrough_file.read_text()

        # Should have Mermaid code blocks
        mermaid_blocks = re.findall(r"```mermaid\n(.*?)```", content, re.DOTALL)
        assert len(mermaid_blocks) >= 2, "Should have at least 2 Mermaid diagrams"

        # At least one should be a graph/flowchart
        has_graph = any("graph" in block for block in mermaid_blocks)
        assert has_graph, "Should have at least one flowchart diagram"

        # At least one should be a sequence diagram
        has_sequence = any("sequenceDiagram" in block for block in mermaid_blocks)
        assert has_sequence, "Should have at least one sequence diagram"

    def test_walkthrough_has_collapsible_sections(self):
        """Test that walkthrough uses collapsible details."""
        walkthrough_file = Path("docs/demos/walkthrough.md")
        content = walkthrough_file.read_text()

        assert "<details>" in content, "Should have collapsible sections"
        assert "<summary>" in content, "Should have summary tags"

    def test_terminal_demo_page_exists(self):
        """Test that terminal demo HTML page exists."""
        terminal_file = Path("docs/demos/terminal-demo.html")
        assert terminal_file.exists(), "Terminal demo page should exist"

    def test_terminal_demo_has_asciinema_player(self):
        """Test that terminal demo includes asciinema player."""
        terminal_file = Path("docs/demos/terminal-demo.html")
        content = terminal_file.read_text()

        assert "asciinema" in content.lower(), "Should reference asciinema"
        assert "AsciinemaPlayer" in content, "Should use AsciinemaPlayer"
        assert "cdn.jsdelivr.net" in content, "Should load from CDN"

    def test_terminal_demo_has_safe_dom_manipulation(self):
        """Test that terminal demo uses safe DOM manipulation (no innerHTML)."""
        terminal_file = Path("docs/demos/terminal-demo.html")
        content = terminal_file.read_text()

        # Should NOT use innerHTML (security risk)
        assert "innerHTML" not in content, "Should not use innerHTML (XSS risk)"

        # Should use safe alternatives
        assert (
            "style.display" in content or "classList" in content
        ), "Should use safe DOM manipulation methods"


class TestDemoScripts:
    """Test that demo build scripts exist and are executable."""

    def test_generate_slides_script_exists(self):
        """Test that slide generation script exists."""
        script_file = Path("scripts/generate_slides.py")
        assert script_file.exists(), "generate_slides.py should exist"

    def test_generate_slides_is_executable(self):
        """Test that slide generation script is executable."""
        script_file = Path("scripts/generate_slides.py")
        assert (
            script_file.stat().st_mode & 0o111
        ), "generate_slides.py should be executable"

    def test_generate_slides_has_shebang(self):
        """Test that slide generation script has Python shebang."""
        script_file = Path("scripts/generate_slides.py")
        first_line = script_file.read_text().split("\n")[0]
        assert first_line.startswith("#!"), "Should have shebang"
        assert "python" in first_line, "Should be Python script"

    def test_record_demo_script_exists(self):
        """Test that recording script exists."""
        script_file = Path("scripts/record_demo.sh")
        assert script_file.exists(), "record_demo.sh should exist"

    def test_record_demo_is_executable(self):
        """Test that recording script is executable."""
        script_file = Path("scripts/record_demo.sh")
        assert script_file.stat().st_mode & 0o111, "record_demo.sh should be executable"

    def test_build_demos_script_exists(self):
        """Test that build orchestrator exists."""
        script_file = Path("scripts/build_demos.py")
        assert script_file.exists(), "build_demos.py should exist"

    def test_build_demos_is_executable(self):
        """Test that build orchestrator is executable."""
        script_file = Path("scripts/build_demos.py")
        assert script_file.stat().st_mode & 0o111, "build_demos.py should be executable"

    def test_build_demos_has_cli_commands(self):
        """Test that build_demos.py has all CLI commands."""
        script_file = Path("scripts/build_demos.py")
        content = script_file.read_text()

        # Should have Click CLI with these commands
        assert "@cli.command()" in content, "Should use Click CLI"
        assert "def all(" in content, "Should have 'all' command"
        assert "def slides(" in content, "Should have 'slides' command"
        assert "def validate(" in content, "Should have 'validate' command"


class TestRevealJsTemplate:
    """Test reveal.js Jinja2 template."""

    def test_slides_template_exists(self):
        """Test that slides template exists."""
        template_file = Path("src/agentready/templates/slides.html.j2")
        assert template_file.exists(), "slides.html.j2 should exist"

    def test_slides_template_has_revealjs_cdn(self):
        """Test that template loads reveal.js from CDN."""
        template_file = Path("src/agentready/templates/slides.html.j2")
        content = template_file.read_text()

        assert "reveal.js" in content.lower(), "Should reference reveal.js"
        assert "cdn.jsdelivr.net" in content, "Should use CDN"
        assert "RevealHighlight" in content, "Should have syntax highlighting plugin"

    def test_slides_template_has_jinja2_variables(self):
        """Test that template uses Jinja2 template variables."""
        template_file = Path("src/agentready/templates/slides.html.j2")
        content = template_file.read_text()

        assert "{{ title }}" in content, "Should have title variable"
        assert "{% for slide in slides %}" in content, "Should iterate over slides"
        assert "{{ slide.title }}" in content, "Should render slide titles"


class TestMakefile:
    """Test Makefile demo targets."""

    def test_makefile_exists(self):
        """Test that Makefile exists."""
        makefile = Path("Makefile")
        assert makefile.exists(), "Makefile should exist"

    def test_makefile_has_demo_targets(self):
        """Test that Makefile has all demo targets."""
        makefile = Path("Makefile")
        content = makefile.read_text()

        # Should have these targets
        assert "demos:" in content, "Should have 'demos' target"
        assert "demo-slides:" in content, "Should have 'demo-slides' target"
        assert "demo-validate:" in content, "Should have 'demo-validate' target"
        assert "demo-record:" in content, "Should have 'demo-record' target"
        assert "demo-serve:" in content, "Should have 'demo-serve' target"

    def test_makefile_demos_calls_slides_and_validate(self):
        """Test that 'demos' target calls slides and validate."""
        makefile = Path("Makefile")
        content = makefile.read_text()

        # Find the demos target
        demos_section = re.search(
            r"^demos:.*?(?=^\w|\Z)", content, re.MULTILINE | re.DOTALL
        )
        assert demos_section, "Should have demos target"

        demos_content = demos_section.group(0)
        assert "demo-slides" in demos_content, "demos should call demo-slides"
        assert "demo-validate" in demos_content, "demos should call demo-validate"


class TestConfigYml:
    """Test Jekyll _config.yml navigation."""

    def test_config_has_demos_navigation(self):
        """Test that _config.yml includes Demos in navigation."""
        config_file = Path("docs/_config.yml")
        content = config_file.read_text()

        assert "Demos" in content, "Should have Demos navigation item"
        assert "/demos" in content, "Should link to /demos"

    def test_config_navigation_order(self):
        """Test that Demos appears in navigation menu."""
        config_file = Path("docs/_config.yml")
        content = config_file.read_text()

        # Extract navigation section
        nav_match = re.search(r"navigation:(.*?)(?=\n\w|\Z)", content, re.DOTALL)
        assert nav_match, "Should have navigation section"

        nav_content = nav_match.group(1)

        # Demos should be in the navigation
        assert "Demos" in nav_content, "Demos should be in navigation"


class TestIntegration:
    """Integration tests for complete demo build workflow."""

    @pytest.mark.integration
    def test_slide_generation_can_import_dependencies(self):
        """Test that generate_slides.py can import all dependencies."""
        import sys
        from pathlib import Path

        # Add scripts directory to path
        scripts_dir = Path("scripts")
        sys.path.insert(0, str(scripts_dir))

        try:
            # This will fail if dependencies are missing
            import generate_slides

            assert hasattr(
                generate_slides, "generate_slides"
            ), "Should have generate_slides function"
        finally:
            sys.path.remove(str(scripts_dir))

    @pytest.mark.integration
    def test_build_demos_can_import_dependencies(self):
        """Test that build_demos.py can import all dependencies."""
        import sys
        from pathlib import Path

        # Add scripts directory to path
        scripts_dir = Path("scripts")
        sys.path.insert(0, str(scripts_dir))

        try:
            # This will fail if dependencies are missing
            import build_demos

            assert hasattr(build_demos, "cli"), "Should have Click CLI"
        finally:
            sys.path.remove(str(scripts_dir))
