"""Unit tests for the research updater's industry source fetching."""

from unittest.mock import MagicMock, patch

# We can't import ResearchUpdater directly because it requires ANTHROPIC_API_KEY
# and a valid config/report file. We'll patch those in a fixture.

SAMPLE_CONFIG = {
    "update_settings": {
        "max_updates_per_run": 5,
        "min_citation_quality_score": 0.7,
        "search_recency_months": 12,
        "max_total_results": 15,
    },
    "priority_attributes": ["5.1"],
    "search_domains": {
        "rss_feeds": [
            {
                "name": "Test Blog",
                "domain": "test.blog",
                "feed_url": "https://test.blog/feed/",
                "format": "rss",
                "max_results": 3,
                "relevance_keywords": ["AI", "agent", "code"],
            },
            {
                "name": "Test Atom",
                "domain": "test.atom",
                "feed_url": "https://test.atom/feed.atom",
                "format": "atom",
                "max_results": 3,
                "relevance_keywords": ["testing", "development"],
            },
        ],
        "sitemap_sources": [
            {
                "name": "Test Site",
                "domain": "test.site",
                "sitemap_url": "https://test.site/sitemap.xml",
                "path_filters": ["/blog/"],
                "max_results": 3,
                "relevance_keywords": ["agent", "code"],
            },
        ],
        "curated_sources": [
            {
                "name": "Test Guide",
                "domain": "test.guide",
                "urls": ["https://test.guide/best-practices"],
                "source_label": "TestGuide",
            },
        ],
        "prioritized": ["test.blog", "arxiv.org"],
        "blocked": ["spam.example.com"],
    },
}

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Blog</title>
    <item>
      <title>AI Agents for Code Review</title>
      <link>https://test.blog/ai-agents-code-review</link>
      <description>How AI agents improve code review workflows.</description>
      <pubDate>Sat, 01 Mar 2025 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Company Picnic Recap</title>
      <link>https://test.blog/picnic</link>
      <description>Photos from the annual company picnic.</description>
      <pubDate>Fri, 28 Feb 2025 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>New Agent Framework Released</title>
      <link>https://test.blog/agent-framework</link>
      <description>Our new agent framework for developers.</description>
      <pubDate>Thu, 27 Feb 2025 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""

SAMPLE_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom Feed</title>
  <entry>
    <title>Testing Best Practices in 2025</title>
    <link href="https://test.atom/testing-2025"/>
    <summary>Modern testing approaches for development teams.</summary>
    <published>2025-03-01T10:00:00Z</published>
  </entry>
  <entry>
    <title>Unrelated Entry</title>
    <link href="https://test.atom/unrelated"/>
    <summary>Nothing to do with our keywords.</summary>
    <published>2025-02-28T10:00:00Z</published>
  </entry>
</feed>"""

SAMPLE_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://test.site/blog/ai-agent-best-practices</loc>
    <lastmod>2025-03-01</lastmod>
  </url>
  <url>
    <loc>https://test.site/blog/code-review-tools</loc>
    <lastmod>2025-02-15</lastmod>
  </url>
  <url>
    <loc>https://test.site/about</loc>
    <lastmod>2024-01-01</lastmod>
  </url>
</urlset>"""

SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>AI Agent Best Practices | Test Site</title>
  <meta name="description" content="A guide to building effective AI agents for code.">
</head>
<body><p>Content here.</p></body>
</html>"""

SAMPLE_HTML_OG = """<!DOCTYPE html>
<html>
<head>
  <title>Page Title</title>
  <meta property="og:description" content="OpenGraph description fallback.">
</head>
<body></body>
</html>"""

SAMPLE_MARKDOWN = """# AGENTS.md Specification

A standard for defining agent instructions in repositories.

This spec provides a way to configure AI coding agents."""


def _make_updater(config=None):
    """Create a ResearchUpdater with mocked dependencies."""
    from scripts.update_research import ResearchUpdater

    cfg = config or SAMPLE_CONFIG
    with (
        patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}),
        patch.object(ResearchUpdater, "_load_config", return_value=cfg),
        patch("anthropic.Anthropic"),
        patch.object(ResearchUpdater, "__init__", lambda self, **kw: None),
    ):
        updater = ResearchUpdater.__new__(ResearchUpdater)
        updater.config = cfg
        updater.changes_made = []
    return updater


class TestExtractHtmlMetadata:
    def test_extracts_title_and_description(self):
        updater = _make_updater()
        result = updater._extract_html_metadata(SAMPLE_HTML)
        assert result["title"] == "AI Agent Best Practices"
        assert "effective AI agents" in result["description"]

    def test_og_description_fallback(self):
        updater = _make_updater()
        result = updater._extract_html_metadata(SAMPLE_HTML_OG)
        assert result["title"] == "Page Title"
        assert result["description"] == "OpenGraph description fallback."

    def test_empty_html(self):
        updater = _make_updater()
        result = updater._extract_html_metadata("")
        assert result["title"] == ""
        assert result["description"] == ""

    def test_malformed_html_no_crash(self):
        updater = _make_updater()
        result = updater._extract_html_metadata("<html><head><title>Unclosed")
        # HTMLParser may or may not capture unclosed title; just ensure no crash
        assert isinstance(result["title"], str)
        assert isinstance(result["description"], str)

    def test_no_meta_description(self):
        updater = _make_updater()
        html = "<html><head><title>Just Title</title></head></html>"
        result = updater._extract_html_metadata(html)
        assert result["title"] == "Just Title"
        assert result["description"] == ""


class TestKeywordMatch:
    def test_query_word_match(self):
        updater = _make_updater()
        assert updater._keyword_match("AI agents for coding", "agent", [])

    def test_keyword_list_match(self):
        updater = _make_updater()
        assert updater._keyword_match("modern development tools", "", ["development"])

    def test_no_match(self):
        updater = _make_updater()
        assert not updater._keyword_match("company picnic photos", "agent", ["code"])

    def test_case_insensitive(self):
        updater = _make_updater()
        assert updater._keyword_match("AI AGENT Framework", "agent", [])

    def test_short_words_ignored(self):
        updater = _make_updater()
        assert not updater._keyword_match("some text here", "an", [])


class TestSearchRssFeeds:
    def _mock_fetch(self, url_to_content):
        def _fetch(url, timeout=15):
            return url_to_content.get(url)

        return _fetch

    def test_rss_parsing_and_keyword_filtering(self):
        updater = _make_updater()
        updater._fetch_url = self._mock_fetch({"https://test.blog/feed/": SAMPLE_RSS})

        results = updater._search_rss_feeds("AI agent")
        titles = [r["title"] for r in results]
        assert "AI Agents for Code Review" in titles
        assert "New Agent Framework Released" in titles
        # "Company Picnic Recap" should be filtered out
        assert "Company Picnic Recap" not in titles

    def test_atom_parsing(self):
        updater = _make_updater()
        updater._fetch_url = self._mock_fetch(
            {
                "https://test.blog/feed/": SAMPLE_RSS,
                "https://test.atom/feed.atom": SAMPLE_ATOM,
            }
        )

        results = updater._search_rss_feeds("testing")
        titles = [r["title"] for r in results]
        assert "Testing Best Practices in 2025" in titles

    def test_max_results_respected(self):
        updater = _make_updater()
        # RSS has 2 matching items, max_results is 3, so all should be returned
        updater._fetch_url = self._mock_fetch({"https://test.blog/feed/": SAMPLE_RSS})
        results = updater._search_rss_feeds("AI agent")
        assert len(results) <= 3

    def test_feed_fetch_failure(self):
        updater = _make_updater()
        updater._fetch_url = self._mock_fetch({})
        results = updater._search_rss_feeds("AI agent")
        assert results == []

    def test_no_feeds_configured(self):
        config = {**SAMPLE_CONFIG, "search_domains": {"rss_feeds": []}}
        updater = _make_updater(config)
        results = updater._search_rss_feeds("AI agent")
        assert results == []

    def test_html_tags_stripped_from_rss_description(self):
        updater = _make_updater()
        rss_with_html = SAMPLE_RSS.replace(
            "How AI agents improve code review workflows.",
            "<p>How <b>AI agents</b> improve code review.</p>",
        )
        updater._fetch_url = self._mock_fetch(
            {"https://test.blog/feed/": rss_with_html}
        )
        results = updater._search_rss_feeds("AI agent")
        for r in results:
            assert "<" not in r["snippet"]


class TestSearchSitemaps:
    def _mock_fetch(self, url_to_content):
        def _fetch(url, timeout=15):
            return url_to_content.get(url)

        return _fetch

    @patch("time.sleep")
    def test_sitemap_parsing_and_path_filtering(self, mock_sleep):
        updater = _make_updater()
        updater._fetch_url = self._mock_fetch(
            {
                "https://test.site/sitemap.xml": SAMPLE_SITEMAP,
                "https://test.site/blog/ai-agent-best-practices": SAMPLE_HTML,
                "https://test.site/blog/code-review-tools": SAMPLE_HTML,
            }
        )

        results = updater._search_sitemaps("AI agent")
        urls = [r["url"] for r in results]
        # /blog/ paths matched, /about excluded by path_filter
        assert "https://test.site/about" not in urls
        # At least one blog URL should match
        assert any("blog" in u for u in urls)

    @patch("time.sleep")
    def test_rate_limiting(self, mock_sleep):
        updater = _make_updater()
        updater._fetch_url = self._mock_fetch(
            {
                "https://test.site/sitemap.xml": SAMPLE_SITEMAP,
                "https://test.site/blog/ai-agent-best-practices": SAMPLE_HTML,
                "https://test.site/blog/code-review-tools": SAMPLE_HTML,
            }
        )

        updater._search_sitemaps("AI agent")
        assert mock_sleep.call_count > 0
        mock_sleep.assert_called_with(0.5)

    @patch("time.sleep")
    def test_sitemap_fetch_failure(self, mock_sleep):
        updater = _make_updater()
        updater._fetch_url = self._mock_fetch({})
        results = updater._search_sitemaps("AI agent")
        assert results == []


class TestSearchCuratedSources:
    def _mock_fetch(self, url_to_content):
        def _fetch(url, timeout=15):
            return url_to_content.get(url)

        return _fetch

    def test_html_curated_source(self):
        updater = _make_updater()
        updater._fetch_url = self._mock_fetch(
            {"https://test.guide/best-practices": SAMPLE_HTML}
        )

        results = updater._search_curated_sources("testing")
        assert len(results) == 1
        assert results[0]["source"] == "TestGuide"
        assert results[0]["title"] == "AI Agent Best Practices"

    def test_markdown_curated_source(self):
        config = {
            **SAMPLE_CONFIG,
            "search_domains": {
                **SAMPLE_CONFIG["search_domains"],
                "curated_sources": [
                    {
                        "name": "AGENTS.md",
                        "domain": "agents.md",
                        "urls": [
                            "https://raw.githubusercontent.com/agentsmd/agents.md/main/README.md"
                        ],
                        "source_label": "AGENTS.md",
                    },
                ],
            },
        }
        updater = _make_updater(config)
        updater._fetch_url = self._mock_fetch(
            {
                "https://raw.githubusercontent.com/agentsmd/agents.md/main/README.md": SAMPLE_MARKDOWN
            }
        )

        results = updater._search_curated_sources("agents")
        assert len(results) == 1
        assert results[0]["title"] == "AGENTS.md Specification"
        assert "standard" in results[0]["snippet"].lower()

    def test_fetch_failure(self):
        updater = _make_updater()
        updater._fetch_url = self._mock_fetch({})
        results = updater._search_curated_sources("anything")
        assert results == []


class TestSearchRecentResearch:
    def test_deduplication(self):
        updater = _make_updater()
        dup_url = "https://example.com/paper"
        updater._search_arxiv = MagicMock(
            return_value=[
                {
                    "title": "Paper A",
                    "url": dup_url,
                    "snippet": "...",
                    "date": "2025-01",
                    "source": "ArXiv",
                }
            ]
        )
        updater._search_semantic_scholar = MagicMock(
            return_value=[
                {
                    "title": "Paper A (dup)",
                    "url": dup_url,
                    "snippet": "...",
                    "date": "2025",
                    "source": "Semantic Scholar",
                }
            ]
        )
        updater._search_rss_feeds = MagicMock(return_value=[])
        updater._search_sitemaps = MagicMock(return_value=[])
        updater._search_curated_sources = MagicMock(return_value=[])

        results = updater.search_recent_research("1.1", "Test Attribute")
        urls = [r["url"] for r in results]
        assert urls.count(dup_url) == 1

    def test_prioritized_domains_sorted_first(self):
        updater = _make_updater()
        updater._search_arxiv = MagicMock(
            return_value=[
                {
                    "title": "ArXiv Paper",
                    "url": "https://arxiv.org/abs/1234",
                    "snippet": "...",
                    "date": "2025-01-01",
                    "source": "ArXiv",
                }
            ]
        )
        updater._search_semantic_scholar = MagicMock(return_value=[])
        updater._search_rss_feeds = MagicMock(
            return_value=[
                {
                    "title": "Blog Post",
                    "url": "https://test.blog/post",
                    "snippet": "...",
                    "date": "2024-06-01",
                    "source": "Test Blog",
                }
            ]
        )
        updater._search_sitemaps = MagicMock(
            return_value=[
                {
                    "title": "Random Site",
                    "url": "https://random.example.com/page",
                    "snippet": "...",
                    "date": "2025-03-01",
                    "source": "Random",
                }
            ]
        )
        updater._search_curated_sources = MagicMock(return_value=[])

        results = updater.search_recent_research("1.1", "Test")
        # Prioritized domains (test.blog, arxiv.org) should come before random.example.com
        from urllib.parse import urlparse

        def _get_netloc(url):
            return urlparse(url).netloc

        prioritized_urls = [
            r["url"]
            for r in results
            if _get_netloc(r["url"]) in ("test.blog", "arxiv.org")
        ]
        non_prioritized_urls = [
            r["url"] for r in results if _get_netloc(r["url"]) == "random.example.com"
        ]
        if prioritized_urls and non_prioritized_urls:
            first_priority_idx = next(
                i for i, r in enumerate(results) if r["url"] in prioritized_urls
            )
            first_non_priority_idx = next(
                i for i, r in enumerate(results) if r["url"] in non_prioritized_urls
            )
            assert first_priority_idx < first_non_priority_idx

    def test_max_total_results_limit(self):
        updater = _make_updater()
        many_results = [
            {
                "title": f"Paper {i}",
                "url": f"https://example.com/paper-{i}",
                "snippet": "...",
                "date": "2025-01",
                "source": "ArXiv",
            }
            for i in range(20)
        ]
        updater._search_arxiv = MagicMock(return_value=many_results)
        updater._search_semantic_scholar = MagicMock(return_value=[])
        updater._search_rss_feeds = MagicMock(return_value=[])
        updater._search_sitemaps = MagicMock(return_value=[])
        updater._search_curated_sources = MagicMock(return_value=[])

        results = updater.search_recent_research("1.1", "Test")
        assert len(results) <= 15

    def test_all_sources_called(self):
        updater = _make_updater()
        updater._search_arxiv = MagicMock(return_value=[])
        updater._search_semantic_scholar = MagicMock(return_value=[])
        updater._search_rss_feeds = MagicMock(return_value=[])
        updater._search_sitemaps = MagicMock(return_value=[])
        updater._search_curated_sources = MagicMock(return_value=[])

        updater.search_recent_research("1.1", "Test Attribute")

        updater._search_arxiv.assert_called_once_with("Test Attribute")
        updater._search_semantic_scholar.assert_called_once_with("Test Attribute")
        updater._search_rss_feeds.assert_called_once_with("Test Attribute")
        updater._search_sitemaps.assert_called_once_with("Test Attribute")
        updater._search_curated_sources.assert_called_once_with("Test Attribute")
