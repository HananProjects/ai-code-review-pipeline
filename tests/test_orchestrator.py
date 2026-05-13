"""Unit tests for the orchestrator synthesis logic (no API calls)."""
from orchestrator.crew import synthesize_comment


def _make_results(sec="pass", perf="pass", style="pass") -> dict:
    return {
        "security": f"Security report content.\nOverall risk: {sec}",
        "performance": f"Performance report content.\nPerformance verdict: {perf}",
        "style": f"Style report content.\nQuality verdict: {style}",
    }


def test_all_pass_gives_pass_overall():
    comment = synthesize_comment(_make_results(), "org/repo", 42)
    assert "PASS" in comment
    assert "BLOCK" not in comment


def test_single_block_escalates_overall():
    comment = synthesize_comment(_make_results(sec="block"), "org/repo", 42)
    assert comment.count("BLOCK") >= 1


def test_warn_without_block_gives_warn():
    comment = synthesize_comment(_make_results(perf="warn"), "org/repo", 42)
    assert "WARN" in comment
    assert "BLOCK" not in comment


def test_comment_contains_all_sections():
    comment = synthesize_comment(_make_results(), "org/repo", 1)
    assert "Security Review" in comment
    assert "Performance Review" in comment
    assert "Style Review" in comment


def test_agent_failure_is_included():
    results = {
        "security": "_Agent failed: timeout_",
        "performance": "All good.\nPerformance verdict: pass",
        "style": "Clean code.\nQuality verdict: pass",
    }
    comment = synthesize_comment(results, "org/repo", 5)
    assert "Agent failed" in comment
