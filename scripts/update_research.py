#!/usr/bin/env python3
"""
Automated research update script for RESEARCH_REPORT.md

Searches for recent research using real APIs (ArXiv, Semantic Scholar),
validates citations, and proposes updates with verified sources.
"""

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic
import yaml


class ResearchUpdater:
    """Manages research report updates with real search and LLM analysis."""

    def __init__(self, config_path: str = "scripts/research_config.yaml"):
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        self.config = self._load_config(config_path)

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        self.client = anthropic.Anthropic(api_key=api_key)

        # Resolve report path relative to this script
        script_dir = Path(__file__).parent
        self.report_path = (
            script_dir.parent / "src" / "agentready" / "data" / "RESEARCH_REPORT.md"
        )
        if not self.report_path.exists():
            raise FileNotFoundError(f"Report file not found: {self.report_path}")
        self.changes_made = []

    def _load_config(self, path: str) -> dict:
        """Load configuration from YAML file."""
        with open(path) as f:
            return yaml.safe_load(f)

    def search_recent_research(
        self, attribute_id: str, attribute_name: str
    ) -> list[dict[str, str]]:
        """Search for recent research using real APIs.

        Uses ArXiv API and Semantic Scholar API for academic papers.
        Returns results with verified URLs.
        """
        results = []

        # ArXiv search
        arxiv_results = self._search_arxiv(attribute_name)
        results.extend(arxiv_results)

        # Semantic Scholar search
        scholar_results = self._search_semantic_scholar(attribute_name)
        results.extend(scholar_results)

        return results[:10]

    def _search_arxiv(self, query: str) -> list[dict[str, str]]:
        """Search ArXiv API for recent papers."""
        search_query = f"({query}) AND (AI OR LLM OR agent OR code)"
        encoded_query = urllib.parse.quote(search_query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&max_results=5&sortBy=submittedDate&sortOrder=descending"

        results = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "agentready/2.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode("utf-8")

            # Parse Atom XML
            import xml.etree.ElementTree as ET

            root = ET.fromstring(content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns)
                summary = entry.find("atom:summary", ns)
                published = entry.find("atom:published", ns)
                arxiv_id = entry.find("atom:id", ns)

                if title is not None and arxiv_id is not None:
                    paper_url = arxiv_id.text.strip()
                    results.append(
                        {
                            "title": title.text.strip().replace("\n", " "),
                            "url": paper_url,
                            "snippet": (
                                summary.text.strip()[:300]
                                if summary is not None
                                else ""
                            ),
                            "date": (
                                published.text[:10] if published is not None else ""
                            ),
                            "source": "ArXiv",
                        }
                    )
        except Exception as e:
            print(f"  ArXiv search failed: {e}")

        return results

    def _search_semantic_scholar(self, query: str) -> list[dict[str, str]]:
        """Search Semantic Scholar API for recent papers."""
        search_query = f"{query} AI coding agent"
        encoded_query = urllib.parse.quote(search_query)
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit=5&fields=title,url,abstract,year&year=2024-2026"

        results = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "agentready/2.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))

            for paper in data.get("data", []):
                if paper.get("title") and paper.get("url"):
                    results.append(
                        {
                            "title": paper["title"],
                            "url": paper["url"],
                            "snippet": (paper.get("abstract") or "")[:300],
                            "date": str(paper.get("year", "")),
                            "source": "Semantic Scholar",
                        }
                    )
        except Exception as e:
            print(f"  Semantic Scholar search failed: {e}")

        return results

    def validate_url(self, url: str) -> bool:
        """Validate that a URL actually resolves (HTTP HEAD check)."""
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False

            req = urllib.request.Request(
                url, method="HEAD", headers={"User-Agent": "agentready/2.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status < 400
        except Exception:
            return False

    def analyze_relevance(
        self,
        attribute_id: str,
        search_results: list[dict[str, str]],
        current_content: str,
    ) -> dict[str, Any]:
        """Use Claude API to analyze search results and determine relevance."""
        prompt = f"""You are a research analyst maintaining a guide on AI-assisted development best practices.

CURRENT ATTRIBUTE CONTENT:
{current_content[:2000]}

RECENT RESEARCH FINDINGS:
{json.dumps(search_results, indent=2)}

TASK:
1. Analyze each research finding for relevance to the attribute
2. Identify genuinely new insights not already in the current content
3. Suggest specific updates only if they add new, verified information
4. Only cite papers with real URLs from the search results above

REQUIREMENTS:
- Only suggest updates with genuinely new information
- Do NOT fabricate citations — only use URLs from the search results
- Rate overall relevance (0-1 score)

OUTPUT FORMAT (JSON):
{{
    "relevance_score": 0.0-1.0,
    "suggested_updates": "Specific text to add (empty string if no updates needed)",
    "citations": [
        {{
            "title": "Exact title from search results",
            "url": "Exact URL from search results",
            "authors": "Author names if available",
            "date": "Date from search results",
            "key_finding": "1-2 sentence summary"
        }}
    ],
    "reasoning": "Why these updates are relevant or why no updates are needed"
}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
            if json_match:
                content = json_match.group(1)

            return json.loads(content)
        except Exception as e:
            print(f"  Error analyzing relevance: {e}")
            return {
                "relevance_score": 0.0,
                "suggested_updates": "",
                "citations": [],
                "reasoning": f"Analysis failed: {e}",
            }

    def update_attribute_section(
        self, attribute_id: str, analysis_result: dict[str, Any]
    ) -> bool:
        """Update the attribute section in the research report.

        Deduplicates: removes any existing "Recent Research Updates" block
        before inserting the new one.
        """
        min_score = self.config["update_settings"]["min_citation_quality_score"]
        if analysis_result["relevance_score"] < min_score:
            print(
                f"  Skipping: relevance score {analysis_result['relevance_score']:.2f} < {min_score}"
            )
            return False

        if (
            not analysis_result["suggested_updates"]
            and not analysis_result["citations"]
        ):
            print("  Skipping: no updates or citations")
            return False

        # Validate citation URLs before adding
        valid_citations = []
        for cite in analysis_result.get("citations", []):
            url = cite.get("url", "")
            if url and self.validate_url(url):
                valid_citations.append(cite)
            else:
                print(f"  Skipping citation with invalid URL: {url}")

        if not valid_citations and not analysis_result["suggested_updates"]:
            print("  Skipping: no valid citations after URL validation")
            return False

        analysis_result["citations"] = valid_citations

        content = self.report_path.read_text()

        # Find attribute section
        pattern = rf"(### {re.escape(attribute_id)} .*?\n)(.*?)(?=\n###|\n---|\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            print(f"  Warning: Could not find attribute {attribute_id}")
            return False

        section_header = match.group(1)
        section_content = match.group(2)

        # DEDUPLICATION: Remove any existing "Recent Research Updates" blocks
        section_content = re.sub(
            r"\n*\*\*Recent Research Updates \(\d{4}-\d{2}\):\*\*.*?(?=\n\*\*(?!Recent)|$)",
            "",
            section_content,
            flags=re.DOTALL,
        )

        updated_content = section_content

        if analysis_result["suggested_updates"]:
            update_text = analysis_result["suggested_updates"]
            update_header = f"\n\n**Recent Research Updates ({datetime.now().strftime('%Y-%m')}):**\n{update_text}"

            impact_pattern = r"(\*\*Impact on Agent Behavior:\*\*.*?\n)(\n)"
            if re.search(impact_pattern, updated_content, re.DOTALL):
                updated_content = re.sub(
                    impact_pattern,
                    rf"\1{update_header}\2",
                    updated_content,
                    count=1,
                    flags=re.DOTALL,
                )
            else:
                updated_content = update_header + "\n" + updated_content

        if valid_citations:
            citations_text = self._format_citations(valid_citations)

            if "**Citation" in updated_content:
                updated_content = re.sub(
                    r"(\*\*Citations?:\*\*\n)(.*?)(\n\n|\n---|\Z)",
                    rf"\1\2{citations_text}\n\3",
                    updated_content,
                    count=1,
                    flags=re.DOTALL,
                )
            else:
                if "**Example" in updated_content:
                    updated_content = re.sub(
                        r"(\*\*Example)",
                        f"**Citations:**\n{citations_text}\n\n\\1",
                        updated_content,
                        count=1,
                    )
                else:
                    updated_content += f"\n\n**Citations:**\n{citations_text}\n"

        new_section = section_header + updated_content
        new_content = re.sub(pattern, new_section, content, count=1, flags=re.DOTALL)

        self.report_path.write_text(new_content)

        self.changes_made.append(
            {
                "attribute_id": attribute_id,
                "relevance_score": analysis_result["relevance_score"],
                "num_citations": len(valid_citations),
            }
        )

        return True

    def _format_citations(self, citations: list[dict[str, str]]) -> str:
        """Format citations in markdown with URL validation."""
        lines = []
        for cite in citations:
            title = cite.get("title", "Untitled")
            url = cite.get("url", "")

            if url:
                parsed = urllib.parse.urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    continue

                blocked = self.config.get("search_domains", {}).get("blocked", [])
                if any(domain in parsed.netloc for domain in blocked):
                    continue

            authors = cite.get("authors", "Unknown")
            date = cite.get("date", "")
            lines.append(f"- [{title}]({url}) - {authors}, {date}")

        return "\n".join(lines)

    def update_metadata(self):
        """Update version and date in report header."""
        content = self.report_path.read_text()

        today = datetime.now().strftime("%Y-%m-%d")

        # Update YAML frontmatter if present
        if content.startswith("---"):
            content = re.sub(r'(date:\s*")[^"]*(")', rf"\g<1>{today}\g<2>", content)

        # Update markdown body
        content = re.sub(
            r"\*\*Date:\*\* \d{4}-\d{2}-\d{2}", f"**Date:** {today}", content
        )

        # Increment patch version
        version_pattern = r"\*\*Version:\*\* (\d+)\.(\d+)\.(\d+)"
        match = re.search(version_pattern, content)
        if match:
            major, minor, patch = map(int, match.groups())
            new_version = f"{major}.{minor}.{patch + 1}"
            content = re.sub(version_pattern, f"**Version:** {new_version}", content)

            # Also update frontmatter version
            content = re.sub(
                r'(version:\s*")[^"]*(")', rf"\g<1>{new_version}\g<2>", content
            )

        self.report_path.write_text(content)

    def run_update(self) -> bool:
        """Main update orchestration."""
        print("Starting research update...")

        content = self.report_path.read_text()
        attribute_pattern = r"### (\d+\.\d+) (.+?)\n"
        attributes = re.findall(attribute_pattern, content)

        print(f"Found {len(attributes)} attributes to check")

        priority_attrs = self.config.get("priority_attributes", [])
        sorted_attrs = sorted(
            attributes, key=lambda x: (x[0] not in priority_attrs, x[0])
        )

        max_updates = self.config["update_settings"]["max_updates_per_run"]
        updates_made = 0

        for attr_id, attr_name in sorted_attrs:
            if updates_made >= max_updates:
                print(f"\nReached max updates limit ({max_updates})")
                break

            print(f"\nProcessing attribute {attr_id}: {attr_name}")

            section_pattern = rf"### {re.escape(attr_id)} {re.escape(attr_name)}(.*?)(?=\n###|\n---|\Z)"
            match = re.search(section_pattern, content, re.DOTALL)
            if not match:
                print("  Could not extract section content")
                continue
            current_content = match.group(1)

            search_results = self.search_recent_research(attr_id, attr_name)
            if not search_results:
                print("  No recent research found")
                continue

            print(f"  Found {len(search_results)} search results")

            analysis = self.analyze_relevance(attr_id, search_results, current_content)
            print(f"  Relevance score: {analysis['relevance_score']:.2f}")

            if self.update_attribute_section(attr_id, analysis):
                updates_made += 1
                print(f"  Updated attribute {attr_id}")

        if self.changes_made:
            self.update_metadata()
            print(f"\nMade {len(self.changes_made)} updates")
            print("Updated version and date")

            print("\nChanges summary:")
            for change in self.changes_made:
                print(
                    f"  - {change['attribute_id']}: score={change['relevance_score']:.2f}, citations={change['num_citations']}"
                )
        else:
            print("\nNo updates needed")

        return len(self.changes_made) > 0


if __name__ == "__main__":
    try:
        updater = ResearchUpdater()
        changes_made = updater.run_update()
        exit(0 if changes_made else 1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
