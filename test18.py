from agent18 import Issue
import pytest

def test_parse_basic_url():
    # Test valid GitHub issue URL
    url = "https://github.com/aidando73/bitbucket-syntax-highlighting/issues/67"
    issue = Issue(url)
    assert issue.owner == "aidando73"
    assert issue.repo == "bitbucket-syntax-highlighting" 
    assert issue.issue_number == 67

def test_parse_invalid_url():
    # Test invalid URL format
    with pytest.raises(ValueError, match="Expected github.com as the domain"):
        Issue("https://not-github.com/owner/repo/issues/1")

def test_parse_invalid_url_no_issue():
    with pytest.raises(ValueError, match="Invalid GitHub issue URL format"):
        Issue("https://github.com/owner/repo")

def test_parse_invalid_url_no_issue_number():
    with pytest.raises(ValueError, match="Expected an issue number in the URL"):
        Issue("https://github.com/owner/repo/issues/")

