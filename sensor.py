"""Sensor platform for Ather 450X."""
import asyncio
import logging

import aiohttp

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    PERCENTAGE,
    DEVICE_CLASS_TIMESTAMP,
    ATTR_DEVICE_CLASS
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    session = hass.data[DOMAIN][entry.entry_id]["session"]
    scooter_id = hass.data[DOMAIN][entry.entry_id]["scooter_id"]
    api_token = hass.data[DOMAIN][entry.entry_id]["api_token"]

    async_add_entities(
        [
            Ather450XRideSensor(session, scooter_id, api_token), # Show last ride details
        ],
        True,
    )


class Ather450XRideSensor(SensorEntity):
    """Representation of an Ather 450X Ride Details sensor."""

    def __init__(self, session: aiohttp.ClientSession, scooter_id, api_token):
        """Initialize the sensor."""
        self._session = session
        self._scooter_id = scooter_id
        self._api_token = api_token
        self._state = None
        self._attrs = {}
        self._name = "Ather 450X Last Ride"
        self._attr_unique_id = "ather_450x_last_ride"  # Unique ID for the entity

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attrs
    
    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:scooter"  # Or any other relevant icon

    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            rides = await get_ride_details(self._session, self._scooter_id, self._api_token, limit=1, sort_order="desc")
            if rides:
                last_ride = rides[0]
                self._state = dt_util.parse_datetime(last_ride["start_time_tz"])  # Use start time as the state
                self._attrs = {
                    "distance": last_ride["distance"],
                    "duration": last_ride["ride_duration"],
                    "efficiency": last_ride["WhPerKm"],
                    "end_time": dt_util.parse_datetime(last_ride["end_time_tz"]),
                    "start_time": dt_util.parse_datetime(last_ride["start_time_tz"]),
                    "ride_id": last_ride["id"],
                    # Add other relevant ride details here
                }
                _LOGGER.debug(f"Updated state: {self._state}")
            else:
                self._state = None
                self._attrs = {}
                _LOGGER.warning("No ride data found")

        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error fetching data: {e}")
            self._state = None
            self._attrs = {}

from homeassistant.helpers.aiohttp_client import async_get_clientsession

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