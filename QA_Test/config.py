from dataclasses import dataclass
import os


@dataclass
class EnvConfig:
    # Tele-Op backend (app_prismax_tele_op_services)
    scheme: str = os.getenv("TELE_SCHEME", "http")
    host: str = os.getenv("TELE_HOST", "localhost")
    port: int = int(os.getenv("TELE_PORT", "8081"))
    base_path: str = os.getenv("TELE_BASE", "").strip("/")

    # Socket auth (must match users table: users.userid + users.hash_code)
    robot_id: str = os.getenv("ROBOT_ID", "arm1")
    user_id: str = os.getenv("USER_ID", "")
    token: str = os.getenv("TOKEN", "")
    # Multi-robot default (for runners/scripts to reference)
    robots_csv: str = os.getenv("ROBOT_IDS", "arm1,arm2,arm3")

    @property
    def base_url(self) -> str:
        url = f"{self.scheme}://{self.host}:{self.port}"
        if self.base_path:
            url = f"{url}/{self.base_path}"
        return url

    @property
    def robot_ids(self):
        return [r.strip() for r in self.robots_csv.split(",") if r.strip()]


