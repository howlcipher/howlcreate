"""Tests for HowlCreate GitHub Pages documentation and assets."""

from pathlib import Path


def test_docs_assets_exist():
    docs_dir = Path(__file__).parent.parent / "docs"
    assert (docs_dir / "index.html").is_file()
    assert (docs_dir / "style.css").is_file()
    assert (docs_dir / "script.js").is_file()
    assert (docs_dir / "favicon.svg").is_file()
    assert (docs_dir / "favicon.png").is_file()
    assert (docs_dir / "social-preview.png").is_file()
    assert (docs_dir / "social-preview.svg").is_file()


def test_index_html_contains_critical_sections_and_links():
    index_file = Path(__file__).parent.parent / "docs" / "index.html"
    content = index_file.read_text(encoding="utf-8")

    # Required sections
    assert 'id="main-title"' in content
    assert 'id="overview"' in content
    assert 'id="why-create"' in content
    assert 'id="boundary"' in content
    assert 'id="operators"' in content
    assert 'id="pipeline"' in content
    assert 'id="status-cli"' in content

    # Key ecosystem links
    assert "https://howlcipher.github.io/howl/" in content
    assert "https://howlcipher.github.io/howlrelay/" in content
    assert "https://howlcipher.github.io/howlplane/" in content
    assert "https://howlcipher.github.io/howlframe/" in content
    assert "https://howlcipher.github.io/howlchangeops/" in content
    assert "https://github.com/howlcipher/howlcreate" in content
