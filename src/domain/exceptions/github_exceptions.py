from datetime import datetime, timezone


class GitHubBaseException(Exception):
    """Base exception for GitHub related errors"""
    pass


class GitHubAuthenticationError(GitHubBaseException):
    """Raised when GitHub token is invalid"""
    pass


class GitHubAccessError(GitHubBaseException):
    """Raised when access to repository is denied"""
    pass


class GitHubConnectionError(GitHubBaseException):
    """Raised when there's a connection error"""
    pass


class GitHubRateLimitException(GitHubBaseException):
    """Exception raised when GitHub API rate limit is exceeded."""

    def __init__(self, _reset_time: int):
        self.reset_time = datetime.fromtimestamp(_reset_time,
                                                 tz=timezone.utc)  # UTC epoch seconds when rate limit resets
        human_readable_reset = self.reset_time.strftime('%Y-%m-%d %H:%M:%S UTC')
        super().__init__(f"GitHub API rate limit exceeded. Retry after: {human_readable_reset}")


class GitHubNotFoundException(GitHubBaseException):
    """Exception raised when not found resource."""
