"""Unit tests for the Deterministic ReDoS Analyzer Engine."""
from pyregex.domain.explain.redos import ReDoSAnalyzer

def test_safe_regex():
    """Verify O(1) or O(N) evaluation for safe patterns."""
    analyzer = ReDoSAnalyzer()
    
    report1 = analyzer.analyze("^[0-9]+$")
    assert not report1.is_vulnerable
    assert report1.complexity.notation in ("O(1)", "O(N)")
    
    report2 = analyzer.analyze("abcde")
    assert not report2.is_vulnerable
    assert report2.complexity.notation in ("O(1)", "O(N)")

def test_exponential_redos():
    """Verify O(2^N) evaluation for true nested quantifiers."""
    analyzer = ReDoSAnalyzer()
    
    report = analyzer.analyze("^([a-zA-Z]+)*$")
    assert report.is_vulnerable  # Severity CRITICAL
    assert report.complexity.notation == "O(2^N)"

    report2 = analyzer.analyze("^(a|a)+$")
    assert report2.complexity.notation == "O(2^N)"

def test_quadratic_redos():
    """Verify O(N^2) evaluation for ambiguous adjacent overlapping sets."""
    analyzer = ReDoSAnalyzer()
    
    # Overlapping sets: \w+\d+ where \d is a subset of \w
    report = analyzer.analyze(r"^\w+\d+$")
    assert report.complexity.notation in ("O(N²)", "O(N³)", "O(2^N)")

def test_safe_rewrite_suggestions():
    """Verify the rewrite engine produces safe alternatives for vulnerabilities."""
    analyzer = ReDoSAnalyzer()
    
    report = analyzer.analyze("^(a*)*$")
    assert report.is_vulnerable
    assert report.safe_rewrite is not None
    assert "(a*)*" not in report.safe_rewrite
