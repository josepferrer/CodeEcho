from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class ProviderType:
    """Value Object for Provider Type"""
    name: str

    def __post_init__(self):
        valid_providers = {'github', 'gitlab'}
        if self.name.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of {valid_providers}")

    @property
    def value(self) -> str:
        return self.name.lower()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProviderType):
            return NotImplemented
        return self.value == other.value


@dataclass(frozen=True)
class RepositoryId:
    """Value Object for Repository ID"""
    owner: str
    name: str
    provider: ProviderType

    @classmethod
    def from_string(cls, repository_string: str, provider_type: str) -> 'RepositoryId':
        """Create RepositoryId from string representation and provider type"""
        owner, name = repository_string.split('/')
        return cls(
            owner=owner,
            name=name,
            provider=ProviderType(provider_type)
        )

    def __str__(self) -> str:
        return f"{self.owner}/{self.name}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RepositoryId):
            return NotImplemented
        return (self.owner == other.owner and
                self.name == other.name and
                self.provider == other.provider)

    def __hash__(self) -> int:
        return hash((self.owner, self.name, self.provider.value))


@dataclass(frozen=True)
class RateLimit:
    """Value Object for Rate Limit"""
    reset_time: datetime

    def is_exceeded(self, current_time: Optional[datetime] = None) -> bool:
        """Check if we're still within the rate limit period"""
        current = current_time or datetime.utcnow()
        return self.reset_time > current

    def time_until_reset(self, current_time: Optional[datetime] = None) -> Optional[float]:
        """Get seconds until rate limit reset"""
        current = current_time or datetime.utcnow()
        if self.reset_time <= current:
            return None
        return (self.reset_time - current).total_seconds()
