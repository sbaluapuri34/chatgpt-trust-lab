from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from phase3.config import ResearchTheme
from scripts.aggregate import compute_deciles, run_aggregation


@dataclass(frozen=True)
class MockPhase3Config:
    research_themes: tuple[ResearchTheme, ...]
    db_path: Path
    batches_dir: Path


@pytest.fixture
def mock_db_path(tmp_path: Path) -> Path:
    db = tmp_path / "test_research.db"
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    
    # Create the three tables matching Phase 3 schema
    cur.execute("""
        CREATE TABLE posts (
            id TEXT PRIMARY KEY,
            score INTEGER,
            weight REAL,
            url TEXT,
            created_utc REAL,
            title TEXT,
            selftext TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE post_features (
            post_id TEXT PRIMARY KEY,
            match_trust_loss INTEGER,
            is_candidate INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE post_analysis (
            post_id TEXT PRIMARY KEY,
            stage1_relevant INTEGER,
            primary_theme TEXT,
            secondary_themes TEXT,
            severity TEXT,
            evidence_quote TEXT,
            theme_rationale TEXT,
            model_confidence REAL
        )
    """)
    
    # Seed mock data
    # 1. Ingested posts (10 total)
    # Weights are calculated as ln(1 + max(score, 0))
    posts_data = [
        ("p1", 10, 2.398, "http://p1", 1759296000.0, "p1 title", "p1 body text"),
        ("p2", 20, 3.045, "http://p2", 1759296000.0, "p2 title", "p2 body text"),
        ("p3", 30, 3.434, "http://p3", 1759296000.0, "p3 title", "p3 body text"),
        ("p4", 5, 1.792, "http://p4", 1759296000.0, "p4 title", "p4 body text"),
        ("p5", 0, 0.0, "http://p5", 1759296000.0, "p5 title", "p5 body text"),
        ("p6", 15, 2.773, "http://p6", 1759296000.0, "p6 title", "p6 body text"),
        ("p7", 8, 2.197, "http://p7", 1759296000.0, "p7 title", "p7 body text"),
        ("p8", 12, 2.565, "http://p8", 1759296000.0, "p8 title", "p8 body text"),
        ("p9", 100, 4.615, "http://p9", 1759296000.0, "p9 title", "p9 body text"),
        ("p10", 2, 1.099, "http://p10", 1759296000.0, "p10 title", "p10 body text"),
    ]
    cur.executemany("INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?)", posts_data)
    
    # 2. Preselected candidates (8 total candidates, 2 non-candidates)
    features_data = [
        ("p1", 1, 1),
        ("p2", 0, 1),
        ("p3", 1, 1),
        ("p4", 2, 1),
        ("p5", 0, 0), # Not a candidate
        ("p6", 0, 1),
        ("p7", 3, 1),
        ("p8", 0, 1),
        ("p9", 0, 1),
        ("p10", 0, 0), # Not a candidate
    ]
    cur.executemany("INSERT INTO post_features VALUES (?, ?, ?)", features_data)
    
    # 3. Analysis results
    # 6 relevant, 2 irrelevant, 2 not analyzed (is_candidate = 0)
    analysis_data = [
        ("p1", 1, "user_trust_breakdown", "[\"over_reliance_on_ai_outputs\"]", "high", "p1 trust quote", "p1 rationale", 0.9),
        ("p2", 1, "user_trust_breakdown", "[]", "medium", "p2 trust quote", "p2 rationale", 0.9),
        ("p3", 1, "overconfident_incorrect_outputs", "[\"user_trust_breakdown\"]", "high", "p3 hall quote", "p3 rationale", 0.9),
        ("p4", 1, "real_world_impact_of_ai_outputs", "[\"user_trust_breakdown\", \"over_reliance_on_ai_outputs\"]", "high", "p4 cons quote", "p4 rationale", 0.9),
        ("p5", 0, None, None, None, None, None, None), # Irrelevant/not candidate
        ("p6", 1, "user_trust_breakdown", "[]", "low", "p6 trust quote", "p6 rationale", 0.9),
        ("p7", 1, "over_reliance_on_ai_outputs", "[]", "medium", "p7 trust quote", "p7 rationale", 0.9),
        ("p8", 0, None, None, None, None, None, None), # Irrelevant candidate
        ("p9", 0, None, None, None, None, None, None), # Irrelevant candidate
        ("p10", 0, None, None, None, None, None, None), # Irrelevant/not candidate
    ]
    cur.executemany("INSERT INTO post_analysis VALUES (?, ?, ?, ?, ?, ?, ?, ?)", analysis_data)
    
    conn.commit()
    conn.close()
    return db


@pytest.fixture
def mock_config(mock_db_path: Path, tmp_path: Path) -> MockPhase3Config:
    themes = (
        ResearchTheme(slug="user_trust_breakdown", label="User Trust Breakdown"),
        ResearchTheme(slug="overconfident_incorrect_outputs", label="Overconfident but Incorrect Outputs"),
        ResearchTheme(slug="real_world_impact_of_ai_outputs", label="Real-World Impact of AI Outputs"),
        ResearchTheme(slug="over_reliance_on_ai_outputs", label="Over-Reliance on AI Outputs"),
    )
    return MockPhase3Config(
        research_themes=themes,
        db_path=mock_db_path,
        batches_dir=tmp_path / "batches"
    )


def test_compute_deciles() -> None:
    items = [
        {"score": 10},
        {"score": 20},
        {"score": 5},
        {"score": 30},
        {"score": 15},
        {"score": 8},
        {"score": 12},
        {"score": 100},
        {"score": 2},
        {"score": 0},
    ]
    res = compute_deciles(items)
    
    # 10 items total, so deciles should be exactly index + 1 (1 to 10)
    assert res[0]["score"] == 100
    assert res[0]["decile"] == 1
    
    assert res[1]["score"] == 30
    assert res[1]["decile"] == 2
    
    assert res[9]["score"] == 0
    assert res[9]["decile"] == 10


def test_run_aggregation(mock_config: MockPhase3Config, tmp_path: Path) -> None:
    output_dir = tmp_path / "aggregated"
    
    run_aggregation(mock_config, output_dir)
    
    # Verify file existence
    assert (output_dir / "theme_prevalence.csv").exists()
    assert (output_dir / "theme_cooccurrence.json").exists()
    assert (output_dir / "trust_erosion_report.json").exists()
    assert (output_dir / "severity_distribution.csv").exists()
    assert (output_dir / "score_impact.csv").exists()
    assert (output_dir / "representative_quotes.json").exists()
    assert (output_dir / "methodology_snippet.json").exists()
    
    # 1. Verify Theme Prevalence
    prevalence = []
    with (output_dir / "theme_prevalence.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            prevalence.append(r)
            
    assert len(prevalence) > 0
    trust_row = next(r for r in prevalence if r["theme_slug"] == "user_trust_breakdown")
    assert int(trust_row["raw_count"]) == 3
    assert float(trust_row["raw_pct"]) == 50.0  # 3 of 6 relevant posts
    assert float(trust_row["weighted_count"]) == round(2.398 + 3.045 + 2.773, 2)
    
    # 2. Verify Theme Co-occurrence Matrix
    with (output_dir / "theme_cooccurrence.json").open(encoding="utf-8") as f:
        matrix = json.load(f)
        
    # p1 (user_trust_breakdown -> over_reliance_on_ai_outputs)
    assert matrix["user_trust_breakdown"]["over_reliance_on_ai_outputs"] == 1
    # p3 (overconfident_incorrect_outputs -> user_trust_breakdown)
    assert matrix["overconfident_incorrect_outputs"]["user_trust_breakdown"] == 1
    
    # 3. Verify Trust Erosion Report
    with (output_dir / "trust_erosion_report.json").open(encoding="utf-8") as f:
        report = json.load(f)
        
    metrics = report["metrics"]
    assert metrics["total_relevant_posts"] == 6
    
    # p1: trust_erosion + match_trust_loss=1 => TP
    # p2: trust_erosion + match_trust_loss=0 => FP
    # p6: trust_erosion + match_trust_loss=0 => FP
    # p3: other theme + match_trust_loss=1 => FN
    # p4: other theme + match_trust_loss=2 => FN
    # p7: other theme + match_trust_loss=3 => FN
    # Wait, let's verify if p7 has match_trust_loss >= 1. Yes, 3.
    # Let's count them:
    # Labeled trust_erosion: p1 (match_trust_loss=1), p2 (match_trust_loss=0), p6 (match_trust_loss=0).
    # TP = 1 (p1)
    # FP = 2 (p2, p6)
    # Labeled other: p3 (match_trust_loss=1), p4 (match_trust_loss=2), p7 (match_trust_loss=3).
    # FN = 3 (p3, p4, p7)
    # TN = 0
    # Let's see:
    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 2
    assert metrics["false_negatives"] == 3
    assert metrics["true_negatives"] == 0
    assert metrics["precision_of_signal"] == round(1 / 3, 4)
    assert metrics["recall_of_signal"] == round(1 / 4, 4)
    
    # 4. Verify Severity Distribution
    severity = []
    with (output_dir / "severity_distribution.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            severity.append(r)
            
    assert len(severity) > 0
    trust_high = next(r for r in severity if r["theme_slug"] == "user_trust_breakdown" and r["severity"] == "high")
    assert int(trust_high["raw_count"]) == 1
    assert float(trust_high["weighted_count"]) == 2.40  # round(2.398, 2)
    
    # 5. Verify Score Impact
    score_impact = []
    with (output_dir / "score_impact.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            score_impact.append(r)
            
    assert len(score_impact) > 0
    # Checks that all deciles 1-10 are represented
    deciles = {int(r["decile"]) for r in score_impact}
    assert deciles == set(range(1, 11))
    
    # 6. Verify Representative Quotes
    with (output_dir / "representative_quotes.json").open(encoding="utf-8") as f:
        quotes = json.load(f)
        
    assert "user_trust_breakdown" in quotes
    assert len(quotes["user_trust_breakdown"]) == 3
    # Top score should be first: p2 has score 20, p6 has 15, p1 has 10.
    assert quotes["user_trust_breakdown"][0]["score"] == 20
    assert quotes["user_trust_breakdown"][0]["evidence_quote"] == "p2 trust quote"
    assert quotes["user_trust_breakdown"][1]["score"] == 15
    assert quotes["user_trust_breakdown"][2]["score"] == 10
    
    # 7. Verify Methodology Funnel Snippet
    with (output_dir / "methodology_snippet.json").open(encoding="utf-8") as f:
        funnel = json.load(f)
        
    funnel_table = funnel["funnel_table"]
    assert funnel_table["total_ingested_raw_posts"] == 10
    assert funnel_table["preselected_keyword_candidates"] == 8
    # posts p1, p2, p3, p4, p6, p7 have stage1_relevant = 1 (total 6)
    assert funnel_table["stage1_confirmed_relevant_posts"] == 6
    # primary_theme is not null: p1, p2, p3, p4, p6, p7 (total 6)
    assert funnel_table["stage2_deep_theme_analyzed_posts"] == 6
