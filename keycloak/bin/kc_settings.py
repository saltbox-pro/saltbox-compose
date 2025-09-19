import os
import json
import aiofiles.os

from dataclasses import dataclass


@dataclass
class KCSettings:
    server_url: str
    realm: str
    admin_username: str
    admin_password: str
    sb_user_name: str
    sb_user_email: str
    sb_user_firstname: str
    sb_user_lastname: str
    sb_user_password: str
    sb_admin_name: str
    sb_admin_email: str
    sb_admin_firstname: str
    sb_admin_lastname: str
    sb_admin_password: str
    path_to_client_config: str
    path_to_grafana_client_config: str
    
    @classmethod
    async def create(cls) -> "KCSettings":
        return cls(
            # server_url = await cls._get_secret("KEYCLOAK_URL", "http://keycloak:8080/auth"),
            server_url = "http://keycloak:8080/auth/keycloak/",
            realm = os.getenv("KEYCLOAK_REALM", "salt.box"),
            admin_username = "admin",
            admin_password = await cls._get_secret("/run/secrets/keycloak_admin_password"),
            sb_user_name = os.getenv("KEYCLOAK_USER_NAME", "user"),
            sb_user_email = os.getenv("KEYCLOAK_USER_EMAIL", "user@example.com"),
            sb_user_firstname = os.getenv("KEYCLOAK_USER_FIRSTNAME", "Ioann"),
            sb_user_lastname = os.getenv("KEYCLOAK_USER_LASTNAME", "Ivanov"),
            sb_user_password = await cls._get_secret("/run/secrets/saltbox_user_password"),
            sb_admin_name = os.getenv("KEYCLOAK_ADMIN_NAME", "master"),
            sb_admin_email = os.getenv("KEYCLOAK_ADMIN_EMAIL", "master@example.com"),
            sb_admin_firstname = os.getenv("KEYCLOAK_ADMIN_FIRSTNAME", 'Petr'),
            sb_admin_lastname = os.getenv("KEYCLOAK_ADMIN_LASTNAME", 'Petrov'),
            sb_admin_password = await cls._get_secret("/run/secrets/saltbox_admin_password"),
            path_to_client_config = "./client.json",
            path_to_grafana_client_config = "./grafana_client.json",
        )
 
    @staticmethod
    async def _get_secret(key: str, default: str = None) -> str:
        if key.startswith('/run/secrets/'):
            if not await aiofiles.os.path.exists(path=key):
                raise FileNotFoundError(f"Secret file not found: {key}")
            async with aiofiles.open(file=key, mode='r') as f:
                return (await f.read()).strip()
        return os.getenv(key, default)

    @property
    async def config(self) -> dict:
        core_client_config = await self._load_client_config(path=self.path_to_client_config)
        grafana_client_config = await self._load_client_config(path=self.path_to_grafana_client_config)
        return {
            **self.base_realm_config,
            "clients": [core_client_config, grafana_client_config],
            "users": self.users_config
        }

    async def _load_client_config(self, path: str) -> list[dict]:
        if not await aiofiles.os.path.exists(path):
            raise FileNotFoundError(f"Client config not found | Path: {path}")
        async with aiofiles.open(path, 'r') as f:
            content = await f.read()
            return json.loads(content)

    @property
    def base_realm_config(self) -> dict: 
        return {
            "id": self.realm,
            "realm": self.realm,
            "enabled": True,
            "eventsEnabled": True,
            "eventsExpiration": 900,  # 15 min
            "adminEventsEnabled": True,
            "adminEventsDetailsEnabled": True,
            "attributes": {
                "oidc.ciba.grant.enabled": "false",
                "client.secret.creation.time": "1727112859",
                "backchannel.logout.session.required": "true",
                "display.on.consent.screen": "false",
                "oauth2.device.authorization.grant.enabled": "false",
                "adminEventsExpiration": "900",
            },
        }
    
    @property
    def users_config(self) -> list[dict]:
        return [
            {
                "id": self.sb_user_name,
                "email": self.sb_user_email,
                "username": self.sb_user_name,
                "firstName": self.sb_user_firstname,
                "lastName": self.sb_user_lastname,
                "enabled": True,
                "emailVerified": False,
                "credentials": [{"type": "password", "value": self.sb_user_password, "temporary": False}],
                "realmRoles": ["user"],
            },
            {
                "id": self.sb_admin_name,
                "email": self.sb_admin_email,
                "username": self.sb_admin_name,
                "firstName": self.sb_admin_firstname,
                "lastName": self.sb_admin_lastname,
                "enabled": True,
                "emailVerified": False,
                "credentials": [{"type": "password", "value": self.sb_admin_password, "temporary": False}],
                "realmRoles": [
                    "saltbox_admin", "collections_admin", "grafana_admin", "tasks_admin", "jobs_admin",
                    "test_common", "masters_admin", "scheduler_admin"
                ],
            },
        ]
