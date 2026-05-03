#!/usr/bin/env python3
"""
Automated research update script for RESEARCH_REPORT.md

Searches for recent research using real APIs (ArXiv, Semantic Scholar),
validates citations, and proposes updates with verified sources.
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from html.parser import HTMLParser
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
        """Search for recent research using academic APIs and industry sources.

        Uses ArXiv, Semantic Scholar, RSS feeds, sitemaps, and curated URLs.
        Returns deduplicated results sorted by domain priority and date.
        """
        results = []

        # Academic sources
        results.extend(self._search_arxiv(attribute_name))
        results.extend(self._search_semantic_scholar(attribute_name))

        # Industry sources
        results.extend(self._search_rss_feeds(attribute_name))
        results.extend(self._search_sitemaps(attribute_name))
        results.extend(self._search_curated_sources(attribute_name))

        # Deduplicate by URL
        seen_urls: set[str] = set()
        unique: list[dict[str, str]] = []
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                unique.append(r)

        # Sort: prioritized domains first, then newest date first within each group.
        # Two-pass stable sort: first by date desc, then by priority asc.
        prioritized = set(self.config.get("search_domains", {}).get("prioritized", []))

        def _is_priority(r: dict[str, str]) -> bool:
            netloc = urllib.parse.urlparse(r["url"]).netloc.replace("www.", "")
            return any(netloc == p or netloc.endswith("." + p) for p in prioritized)

        unique.sort(key=lambda r: r.get("date") or "0000", reverse=True)
        unique.sort(key=lambda r: 0 if _is_priority(r) else 1)

        max_total = self.config.get("update_settings", {}).get("max_total_results", 15)
        return unique[:max_total]

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

    def _extract_html_metadata(self, html_content: str) -> dict[str, str]:
        """Extract title and description from HTML using stdlib parser."""
        result = {"title": "", "description": ""}

        class _MetadataParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self._in_title = False
                self._title_parts: list[str] = []
                self.title = ""
                self.description = ""

            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
                if tag == "title":
                    self._in_title = True
                if tag == "meta":
                    attr_dict = dict(attrs)
                    name = (attr_dict.get("name") or "").lower()
                    prop = (attr_dict.get("property") or "").lower()
                    content = attr_dict.get("content") or ""
                    if name == "description" and content:
                        self.description = content
                    elif prop == "og:description" and content and not self.description:
                        self.description = content

            def handle_data(self, data: str):
                if self._in_title:
                    self._title_parts.append(data)

            def handle_endtag(self, tag: str):
                if tag == "title" and self._in_title:
                    self._in_title = False
                    self.title = "".join(self._title_parts).strip()

        try:
            parser = _MetadataParser()
            parser.feed(html_content)
            title = parser.title
            # Strip common site-name suffixes
            for sep in [" | ", " - ", " — ", " :: "]:
                if sep in title:
                    title = title.split(sep)[0].strip()
            result["title"] = title
            result["description"] = parser.description[:300]
        except Exception:
            pass

        return result

    def _keyword_match(self, text: str, query: str, keywords: list[str]) -> bool:
        """Check if any query term or keyword appears in text (case-insensitive)."""
        text_lower = text.lower()
        for word in query.lower().split():
            if len(word) > 2 and word in text_lower:
                return True
        for kw in keywords:
            if kw.lower() in text_lower:
                return True
        return False

    def _fetch_url(self, url: str, timeout: int = 15) -> str | None:
        """Fetch a URL and return decoded content, or None on failure."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "agentready/2.0"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception:
            return None

    def _search_rss_feeds(self, query: str) -> list[dict[str, str]]:
        """Search RSS/Atom feeds from configured industry sources."""
        feeds = self.config.get("search_domains", {}).get("rss_feeds", [])
        results = []

        for feed_cfg in feeds:
            feed_name = feed_cfg["name"]
            feed_url = feed_cfg["feed_url"]
            fmt = feed_cfg.get("format", "rss")
            max_results = feed_cfg.get("max_results", 5)
            keywords = feed_cfg.get("relevance_keywords", [])

            try:
                content = self._fetch_url(feed_url)
                if not content:
                    print(f"  {feed_name} feed: no response")
                    continue

                root = ET.fromstring(content)
                feed_results = []

                if fmt == "atom":
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    for entry in root.findall("atom:entry", ns):
                        title_el = entry.find("atom:title", ns)
                        link_el = entry.find("atom:link", ns)
                        summary_el = entry.find("atom:summary", ns)
                        if summary_el is None:
                            summary_el = entry.find("atom:content", ns)
                        published_el = entry.find("atom:published", ns)
                        if published_el is None:
                            published_el = entry.find("atom:updated", ns)

                        title = (
                            title_el.text.strip()
                            if title_el is not None and title_el.text
                            else ""
                        )
                        href = link_el.get("href", "") if link_el is not None else ""
                        snippet = (
                            summary_el.text.strip()[:300]
                            if summary_el is not None and summary_el.text
                            else ""
                        )
                        date = (
                            published_el.text[:10]
                            if published_el is not None and published_el.text
                            else ""
                        )

                        if title and href:
                            combined = f"{title} {snippet}"
                            if self._keyword_match(combined, query, keywords):
                                feed_results.append(
                                    {
                                        "title": title.replace("\n", " "),
                                        "url": href,
                                        "snippet": snippet,
                                        "date": date,
                                        "source": feed_name,
                                    }
                                )
                else:
                    # RSS 2.0
                    channel = root.find("channel")
                    items = channel.findall("item") if channel is not None else []
                    for item in items:
                        title_el = item.find("title")
                        link_el = item.find("link")
                        desc_el = item.find("description")
                        date_el = item.find("pubDate")

                        title = (
                            title_el.text.strip()
                            if title_el is not None and title_el.text
                            else ""
                        )
                        link = (
                            link_el.text.strip()
                            if link_el is not None and link_el.text
                            else ""
                        )
                        snippet = (
                            desc_el.text.strip()[:300]
                            if desc_el is not None and desc_el.text
                            else ""
                        )
                        date = (
                            date_el.text.strip()[:16]
                            if date_el is not None and date_el.text
                            else ""
                        )

                        if title and link:
                            combined = f"{title} {snippet}"
                            if self._keyword_match(combined, query, keywords):
                                feed_results.append(
                                    {
                                        "title": title.replace("\n", " "),
                                        "url": link,
                                        "snippet": re.sub(r"<[^>]+>", "", snippet),
                                        "date": date,
                                        "source": feed_name,
                                    }
                                )

                results.extend(feed_results[:max_results])
            except Exception as e:
                print(f"  {feed_name} feed search failed: {e}")

        return results

    def _search_sitemaps(self, query: str) -> list[dict[str, str]]:
        """Search sitemap-based industry sources for relevant pages."""
        sources = self.config.get("search_domains", {}).get("sitemap_sources", [])
        results = []

        for src in sources:
            src_name = src["name"]
            sitemap_url = src["sitemap_url"]
            path_filters = src.get("path_filters", [])
            max_results = src.get("max_results", 5)
            keywords = src.get("relevance_keywords", [])

            try:
                content = self._fetch_url(sitemap_url)
                if not content:
                    print(f"  {src_name} sitemap: no response")
                    continue

                root = ET.fromstring(content)
                ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                candidates = []
                for url_el in root.findall("sm:url", ns):
                    loc_el = url_el.find("sm:loc", ns)
                    lastmod_el = url_el.find("sm:lastmod", ns)
                    if loc_el is None or not loc_el.text:
                        continue
                    loc = loc_el.text.strip()
                    lastmod = (
                        lastmod_el.text.strip()[:10]
                        if lastmod_el is not None and lastmod_el.text
                        else ""
                    )

                    # Filter by path
                    if path_filters and not any(pf in loc for pf in path_filters):
                        continue

                    # Keyword match on URL slug
                    slug = loc.rstrip("/").split("/")[-1].replace("-", " ")
                    if self._keyword_match(slug, query, keywords):
                        candidates.append({"url": loc, "date": lastmod})

                # Fetch HTML metadata for top candidates
                src_results = []
                for cand in candidates[:max_results]:
                    html = self._fetch_url(cand["url"], timeout=10)
                    if html:
                        meta = self._extract_html_metadata(html)
                        if meta["title"]:
                            src_results.append(
                                {
                                    "title": meta["title"],
                                    "url": cand["url"],
                                    "snippet": meta["description"][:300],
                                    "date": cand["date"],
                                    "source": src_name,
                                }
                            )
                    time.sleep(0.5)

                results.extend(src_results)
            except Exception as e:
                print(f"  {src_name} sitemap search failed: {e}")

        return results

    def _search_curated_sources(self, query: str) -> list[dict[str, str]]:
        """Fetch metadata from curated static URLs."""
        sources = self.config.get("search_domains", {}).get("curated_sources", [])
        results = []

        for src in sources:
            src_name = src["name"]
            source_label = src.get("source_label", src_name)
            urls = src.get("urls", [])

            for url in urls:
                try:
                    content = self._fetch_url(url, timeout=10)
                    if not content:
                        continue

                    # Raw markdown (e.g. GitHub raw URLs)
                    url_netloc = urllib.parse.urlparse(url).netloc
                    is_raw_gh = url_netloc == "raw.githubusercontent.com"
                    if is_raw_gh or url.endswith(".md"):
                        heading = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                        para = re.search(r"\n\n(.+?)(?:\n\n|\Z)", content, re.DOTALL)
                        title = heading.group(1).strip() if heading else src_name
                        snippet = (
                            para.group(1).strip()[:300].replace("\n", " ")
                            if para
                            else ""
                        )
                    else:
                        meta = self._extract_html_metadata(content)
                        title = meta["title"] or src_name
                        snippet = meta["description"][:300]

                    results.append(
                        {
                            "title": title,
                            "url": url,
                            "snippet": snippet,
                            "date": "",
                            "source": source_label,
                        }
                    )
                except Exception as e:
                    print(f"  {src_name} curated fetch failed ({url}): {e}")

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
                netloc = parsed.netloc.replace("www.", "")
                if any(
                    netloc == domain or netloc.endswith("." + domain)
                    for domain in blocked
                ):
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
