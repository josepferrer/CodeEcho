import datetime

import pytest
from aioresponses import aioresponses

from src.domain.exceptions.github_exceptions import (
    GitHubAuthenticationError,
    GitHubConnectionError,
    GitHubBaseException,
    GitHubRateLimitException, GitHubNotFoundException
)
from src.infrastructure.repositories.github_client_impl import GitHubClientImpl


@pytest.fixture
def github_fake_token():
    return "fake_test_token"


@pytest.fixture
def github_client(github_token):
    return GitHubClientImpl(token=github_token)


@pytest.fixture
def github_client_fake_token(github_fake_token):
    return GitHubClientImpl(token=github_fake_token)


@pytest.fixture
def base_url():
    return "https://api.github.com"


@pytest.fixture
def repository():
    return "facebook/react"


@pytest.fixture
def unaccesible_repository():
    return "uber/not-access-repo"


@pytest.mark.slow
@pytest.mark.asyncio
async def test_get_pull_requests_success(
        github_client,
        repository
):
    # Execute the method
    result = await github_client.get_pull_requests(repository)

    # Assertions
    assert len(result) == 100
    pr = result[0]
    assert pr.number == 1
    assert pr.id == '6001916'


@pytest.mark.slow
@pytest.mark.asyncio
async def test_get_pull_requests_with_page(
        github_client,
        repository
):
    page = 20

    result = await github_client.get_pull_requests(repository, page=page)

    assert len(result) == 100
    pr = result[0]
    assert pr.number == 3544
    assert pr.id == '32180052'


@pytest.mark.slow
@pytest.mark.asyncio
async def test_get_pull_requests_with_number(
        github_client,
        repository
):
    number = 5

    result = await github_client.get_pull_request(repository, number)

    assert result.number == number


@pytest.mark.slow
@pytest.mark.asyncio
async def test_get_pull_requests_authentication_error(
        github_client_fake_token,
        repository
):
    with pytest.raises(GitHubAuthenticationError):
        await github_client_fake_token.get_pull_requests(repository)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_get_pull_requests_access_error(
        github_client,
        unaccesible_repository
):
    with pytest.raises(GitHubNotFoundException):
        await github_client.get_pull_requests(unaccesible_repository)


@pytest.mark.asyncio
async def test_get_pull_requests_rate_limit(
        github_client,
        base_url,
        repository
):
    """Test handling of rate limit errors"""
    with aioresponses() as m:
        url = f"{base_url}/repos/{repository}/pulls?direction=asc&page=1&per_page=100&sort=created&state=all"
        headers = {
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': str(int((datetime.datetime.now(datetime.timezone.utc).timestamp() + 3600)))
        }
        m.get(url, status=403, headers=headers)

        with pytest.raises(GitHubRateLimitException):
            await github_client.get_pull_requests(repository)


@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_pull_request_detail_success(
        github_client,
        repository
):
    """Test successful retrieval of a single pull request"""
    pr_number = 1

    result = await github_client.get_pull_request(repository, pr_number)

    assert result.id == '6001916'
    assert result.number == pr_number
    assert result.status == 'closed'
    assert result.repository == repository


@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_last_pull_request_number_success(
        github_client,
        repository
):
    """Test successful retrieval of last pr number"""

    result = await github_client.get_last_pull_request_number(repository)

    assert result.number > 32410 # max pr number known at the moment

@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_last_pull_request_number_no_exist(
        github_client
):
    """Test successful retrieval of last pr number"""

    result = await github_client.get_last_pull_request_number("josepferrer/ansible-aws-kinesis-agent")

    assert result is None


@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_pull_request_not_found(
        github_client,
        repository
):
    """Test handling of non-existent pull request"""
    pr_number = 99999999

    with pytest.raises(GitHubBaseException):
        await github_client.get_pull_request(repository, pr_number)


@pytest.mark.asyncio
async def test_connection_timeout(
        github_client,
        base_url,
        repository
):
    """Test handling of connection timeouts"""
    with aioresponses() as m:
        url = f"{base_url}/repos/{repository}/pulls"
        m.get(url, exception=TimeoutError())

        with pytest.raises(GitHubConnectionError):
            await github_client.get_pull_requests(repository)
