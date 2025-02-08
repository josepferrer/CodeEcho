from pathlib import Path
import logging

class ApplicationConfig:
    def __init__(self, github_token: str = None, base_data: str = "data"):
        self.base_data = base_data or "data"
        self.github_token = github_token
        logging.basicConfig(
            level=logging.INFO,  # Cambia a DEBUG si necesitas más detalle
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                         # logging.StreamHandler(sys.stdout),
                         logging.FileHandler(base_data + "/app.log"),
                     ]
        )

    @property
    def pull_request_db_path(self) -> Path:
        return Path(self.base_data) / "prs.db"

    @property
    def sync_state_db_path(self) -> Path:
        return Path(self.base_data) / "sync.db"