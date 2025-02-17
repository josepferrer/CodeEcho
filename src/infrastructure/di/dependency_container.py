from pathlib import Path

from src.application.events import event_bus
from src.application.events.handlers.pull_request_synced_handler import PullRequestSyncedHandler
from src.application.services.sync_pull_requests_service import SyncPullRequestsService
from src.application.services.sync_state_service import SyncStateService
from src.domain.events.pull_request_synced import PullRequestSynced
from src.infrastructure.config.application_config import ApplicationConfig
from src.infrastructure.event_bus.event_bus_provider import EventBusProvider
from src.infrastructure.repositories.github_client_impl import GitHubClientImpl
from src.infrastructure.repositories.sqlite_config import SQLiteConfig
from src.infrastructure.repositories.sqlite_pull_request_repository import SQLitePullRequestRepository
from src.infrastructure.repositories.sqlite_sync_state_repository import SQLiteSyncStateRepository


class DependencyContainer:

    def __init__(self, config: ApplicationConfig):
        self.config = config

        # Database Repositories
        self.sqlite_config_pull_request = SQLiteConfig.create(db_path=config.pull_request_db_path)
        self.pull_request_repository = SQLitePullRequestRepository(self.sqlite_config_pull_request)

        self.sqlite_config_sync_state = SQLiteConfig.create(db_path=config.sync_state_db_path)
        self.sync_state_repository = SQLiteSyncStateRepository(self.sqlite_config_sync_state)

        # API Clients
        self.github_client = GitHubClientImpl(token=config.github_token)

        self.event_bus  = EventBusProvider.get_instance()

        # Services
        self.sync_service = SyncPullRequestsService(self.sync_state_repository, self.github_client,
                                                    self.pull_request_repository, self.event_bus)
        self.sync_state_service = SyncStateService(self.sync_state_repository, self.event_bus)
