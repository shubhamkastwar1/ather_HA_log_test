"""Config flow for Ather 450X integration."""
import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import (
    CONF_USERNAME,  # Not used, but good practice to keep
    CONF_PASSWORD,  # Not used, but good practice to keep
)

from .const import DOMAIN, CONF_SCOOTER_ID, CONF_API_TOKEN

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ather 450X."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                #  Replace with your actual authentication logic
                session = aiohttp.ClientSession()
                # Dummy call to validate the token and scooter ID are working
                ride_data = await get_ride_details(session, user_input[CONF_SCOOTER_ID], user_input[CONF_API_TOKEN], limit=1) # Implement this function
                if ride_data is None:
                    raise Exception("Invalid scooter ID or API token")

            except Exception:  #  Replace with more specific exceptions
                errors["base"] = "invalid_auth"
            else:
                await session.close()
                return self.async_create_entry(title="Ather 450X", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_SCOOTER_ID): str,
                vol.Required(CONF_API_TOKEN): str,
            }),
            errors=errors,
        )
    
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
