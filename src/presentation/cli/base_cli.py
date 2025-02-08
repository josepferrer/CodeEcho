from abc import ABC

import click

from src.infrastructure.config.application_config import ApplicationConfig
from src.infrastructure.config.dependency_container import DependencyContainer


class Cli(ABC):

    @staticmethod
    def service_container(github_token: str = None, db_path: str = None) -> DependencyContainer:
        config = ApplicationConfig(base_data=db_path, github_token=github_token)
        return DependencyContainer(config)

    @staticmethod
    def parse_repository(repository: str) -> tuple[str, str]:
        """Parse repository string into owner and name"""
        try:
            owner, name = repository.split('/')
            return owner, name
        except ValueError:
            raise click.BadParameter(
                "Repository must be in format 'owner/name'"
            )
