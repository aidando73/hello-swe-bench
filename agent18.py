import argparse
from typing import Tuple
import requests

def main(
    issue_url: str,
):
    print(f"Solving issue {issue_url}")
    
class Issue:
    repo: str
    owner: str
    issue_number: int

    def __init__(self, url: str):
        """
        Parse the issue url into the owner, repo and issue number
        """
        # Truncate the https:// prefix if it exists
        if url.startswith("https://"):
            the_url = url[len("https://"):]
        else:
            the_url = url

        # Check that the domain is github.com
        if not the_url.startswith("github.com"):
            raise ValueError(f"Expected github.com as the domain: {url}")

        parts = the_url.split("/")
        if len(parts) < 6:
            raise ValueError("Invalid GitHub issue URL format")
            
        self.owner = parts[3]  # Repository owner/organization
        self.repo = parts[4]   # Repository name
        self.issue_number = parts[6]  # Issue number



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--issue-url",
        type=str,
        required=True,
        help="The issue url to solve. E.g., https://github.com/aidando73/bitbucket-syntax-highlighting/issues/67",
    )
    args = parser.parse_args()
    main(issue_url=args.issue_url)
