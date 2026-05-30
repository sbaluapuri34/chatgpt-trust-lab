from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from phase5.dashboard import get_db_connection, load_aggregates


def test_dashboard_imports() -> None:
    """Ensure modules can be imported without syntax errors."""
    import app
    import phase5.dashboard
    assert app is not None
    assert phase5.dashboard is not None


def test_get_db_connection_read_only(tmp_path: Path) -> None:
    """Verify that get_db_connection opens database strictly in read-only mode."""
    db_file = tmp_path / "test_read_only.db"
    
    # Create seed database
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE test_table (id INTEGER)")
    conn.execute("INSERT INTO test_table VALUES (42)")
    conn.commit()
    conn.close()
    
    # Connect with read-only helper
    ro_conn = get_db_connection(db_file)
    assert isinstance(ro_conn, sqlite3.Connection)
    
    # Assert we can read from it
    val = ro_conn.execute("SELECT id FROM test_table").fetchone()[0]
    assert val == 42
    
    # Assert that writes fail because it is read-only
    with pytest.raises(sqlite3.OperationalError):
        ro_conn.execute("INSERT INTO test_table VALUES (100)")
        
    ro_conn.close()


def test_load_aggregates_empty(tmp_path: Path) -> None:
    """Ensure load_aggregates handles empty directories gracefully by returning an empty dict."""
    res = load_aggregates(tmp_path)
    assert isinstance(res, dict)
    assert len(res) == 0


def test_load_aggregates_populated(tmp_path: Path) -> None:
    """Ensure load_aggregates correctly loads structured CSV and JSON files."""
    # Seed mock files
    (tmp_path / "theme_prevalence.csv").write_text("theme_slug,theme_label,raw_count,raw_pct,weighted_count,weighted_pct\nt1,Theme 1,10,100,10.0,100.0\n", encoding="utf-8")
    (tmp_path / "theme_cooccurrence.json").write_text('{"t1": {"t2": 5}}', encoding="utf-8")
    (tmp_path / "trust_erosion_report.json").write_text('{"metrics": {"f1_score": 0.8}}', encoding="utf-8")
    (tmp_path / "severity_distribution.csv").write_text("theme_slug,severity,raw_count\nt1,high,10\n", encoding="utf-8")
    (tmp_path / "score_impact.csv").write_text("decile,theme_slug,raw_count\n1,t1,10\n", encoding="utf-8")
    (tmp_path / "representative_quotes.json").write_text('{"t1": []}', encoding="utf-8")
    (tmp_path / "methodology_snippet.json").write_text('{"funnel_table": {}}', encoding="utf-8")
    
    res = load_aggregates(tmp_path)
    assert "prevalence" in res
    assert "cooccurrence" in res
    assert "trust_report" in res
    assert "severity" in res
    assert "score_impact" in res
    assert "quotes" in res
    assert "funnel" in res
    
    assert res["prevalence"].iloc[0]["theme_slug"] == "t1"
    assert res["cooccurrence"]["t1"]["t2"] == 5
    assert res["trust_report"]["metrics"]["f1_score"] == 0.8
