"""The Ather 450X integration."""
import asyncio
import logging

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_USERNAME,  # Not used, but good practice to keep
    CONF_PASSWORD,  # Not used, but good practice to keep
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import DOMAIN, CONF_SCOOTER_ID, CONF_API_TOKEN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    vol.Optional(DOMAIN, default={}): vol.Schema({
        vol.Required(CONF_SCOOTER_ID): str,
        vol.Required(CONF_API_TOKEN): str,
    }),
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Ather 450X component from configuration.yaml."""
    # This is only needed if you want to configure via configuration.yaml
    # Most integrations now use config flows.
    conf = config.get(DOMAIN)
    if conf is None:
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data=conf,
        )
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Ather 450X from a config entry."""
    config = entry.data
    scooter_id = config.get(CONF_SCOOTER_ID)
    api_token = config.get(CONF_API_TOKEN)

    try:
        # No authentication needed for this API, but we can use it to validate
        session = aiohttp.ClientSession()
        # Dummy call to validate the token and scooter ID are working
        ride_data = await get_ride_details(session, scooter_id, api_token, limit=1) # Implement this function
        if ride_data is None:
            raise Exception("Invalid scooter ID or API token")

        _LOGGER.debug("Configuration validated successfully")

        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
            "session": session,
            "scooter_id": scooter_id,
            "api_token": api_token,
        }

        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "sensor")
        )
        return True

    except Exception as e:  # Replace with specific exceptions like InvalidAuth
        _LOGGER.error(f"Error during setup: {e}")
        # raise ConfigEntryAuthFailed from e # Use this for authentication errors that should trigger re-authentication

        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    if unload_ok:
        session = hass.data[DOMAIN][entry.entry_id]["session"]
        await session.close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


#  Implement your get_ride_details logic here.  This is a placeholder.
async def get_ride_details(session: aiohttp.ClientSession, scooter_id, api_token, limit=None, sort_order="asc"):
    """Get ride details from the Ather API."""
    url = f"https://cerberus.ather.io/api/v1/triplogs?scooter={scooter_id}&sort=start_time_tz%20{sort_order}"
    if limit is not None:
        url += f"&limit={limit}"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return await response.json()
    except aiohttp.ClientError as e:
        _LOGGER.error(f"Error fetching trip logs for scooter {scooter_id}: {e}")
        return None