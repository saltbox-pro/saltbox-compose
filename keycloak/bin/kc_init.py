import asyncio
import json
import logging

from keycloak import KeycloakAdmin, KeycloakError
from kc_settings import KCSettings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_kc_admin(kc_settings: KCSettings) -> KeycloakAdmin:
    return KeycloakAdmin(
        server_url=kc_settings.server_url,
        username=kc_settings.admin_username,
        password=kc_settings.admin_password,
        client_id="admin-cli",
        verify=True
    )

def handle_kc_error(func_name: str, error: KeycloakError, **kwargs) -> None:
    logger.error("Execution error in '%s' keycloak operation: %s", func_name, str(error))
    if kwargs:
        logger.debug("Error details: %s", json.dumps(obj=kwargs, indent=2))

async def create_entity(
    payload: dict,
    skip_exists: bool,
    entity_type: str,
    create_method: callable,
    log_key: str
) -> None:
    try:
        name = payload.get(log_key, "<unknown>")
        logger.info("Creating %s '%s'...", entity_type, name)

        representation: str = await create_method(payload, skip_exists)
        logger.info("The '%s' %s has been successfully created", name, entity_type)
        
        if isinstance(representation, dict):
            pretty_representation = json.dumps(obj=representation, indent=2)
            logger.debug("%s '%s' representation:\n%s", entity_type.capitalize(), name, pretty_representation)

    except KeycloakError as e:
        handle_kc_error(func_name=str(create_method), error=e, **{log_key: name})
        raise

    except Exception as e:
        logger.error("Unexpected error in '%s': %s", str(create_method), str(e))
        raise

async def create_realm(kc_admin: KeycloakAdmin, payload: dict, skip_exists: bool = False) -> None:
    await create_entity(
        payload=payload,
        skip_exists=skip_exists,
        entity_type="realm",
        create_method=kc_admin.a_create_realm,
        log_key="realm"
    )

async def create_client(kc_admin: KeycloakAdmin, payload: dict, skip_exists: bool = False) -> None:
    await create_entity(
        payload=payload,
        skip_exists=skip_exists,
        entity_type="client",
        create_method=kc_admin.a_create_client,
        log_key="clientId"
    )

async def main() -> None:
    # _ = await kc_admin.a_delete_realm(kc_settings.realm)
    kc_settings = await KCSettings.create()
    kc_admin = create_kc_admin(kc_settings)
    config: dict = await kc_settings.config
    
    await create_realm(kc_admin=kc_admin, payload=kc_settings.base_realm_config, skip_exists=True)
    clients_config: list[dict] = config["clients"]
    
    for client_config in clients_config:
        await create_client(kc_admin=kc_admin, payload=client_config, skip_exists=False)
    
if __name__ == "__main__":
    asyncio.run(main())
