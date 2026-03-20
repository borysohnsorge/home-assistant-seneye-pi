import json
import logging
import types
from datetime import timedelta, datetime, timezone

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_BACKEND, BACKEND_HID, BACKEND_MQTT,
    CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX,
    CONF_UPDATE_INTERVAL_MIN, CONF_TEMP_OFFSET, CONF_PH_OFFSET, CONF_PAR_SCALE,
    DEFAULT_UPDATE_INTERVAL_MIN, DEFAULT_TEMP_OFFSET, DEFAULT_PH_OFFSET, DEFAULT_PAR_SCALE,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "binary_sensor"]
SERVICE_FORCE_UPDATE = "force_update"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    backend = entry.data.get(CONF_BACKEND, BACKEND_HID)
    opts = entry.options or {}
    temp_offset = float(opts.get(CONF_TEMP_OFFSET, DEFAULT_TEMP_OFFSET))
    ph_offset = float(opts.get(CONF_PH_OFFSET, DEFAULT_PH_OFFSET))
    par_scale = float(opts.get(CONF_PAR_SCALE, DEFAULT_PAR_SCALE))

    if backend == BACKEND_MQTT:
        prefix = entry.data.get(CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX)
        coordinator = SeneyeMqttCoordinator(
            hass, prefix=prefix,
            temp_offset=temp_offset, ph_offset=ph_offset, par_scale=par_scale,
        )
        await coordinator.async_subscribe()
    else:
        update_minutes = int(opts.get(CONF_UPDATE_INTERVAL_MIN, DEFAULT_UPDATE_INTERVAL_MIN))
        coordinator = SeneyeDataUpdateCoordinator(
            hass, update_minutes=update_minutes,
            temp_offset=temp_offset, ph_offset=ph_offset, par_scale=par_scale,
        )
        await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if backend == BACKEND_HID:
        async def async_force_update_service(call: ServiceCall) -> None:
            _LOGGER.info("Service '%s.%s' called: forcing refresh", DOMAIN, SERVICE_FORCE_UPDATE)
            await coordinator.async_request_refresh()
        hass.services.async_register(DOMAIN, SERVICE_FORCE_UPDATE, async_force_update_service)

    async def _update_listener(hass: HomeAssistant, updated: ConfigEntry) -> None:
        _LOGGER.debug("Options changed; reloading Seneye")
        await hass.config_entries.async_reload(updated.entry_id)

    entry.async_on_unload(entry.add_update_listener(_update_listener))
    _LOGGER.info("Seneye setup complete (backend=%s)", backend)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if isinstance(coordinator, SeneyeMqttCoordinator):
        coordinator.async_unsubscribe()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        try:
            hass.services.async_remove(DOMAIN, SERVICE_FORCE_UPDATE)
        except Exception:
            pass
    return unload_ok


class SeneyeDataUpdateCoordinator(DataUpdateCoordinator):
    """HID backend — polls SUDevice directly."""

    def __init__(self, hass: HomeAssistant, update_minutes: int,
                 temp_offset: float, ph_offset: float, par_scale: float) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=update_minutes))
        self.temp_offset = float(temp_offset)
        self.ph_offset = float(ph_offset)
        self.par_scale = float(par_scale)
        self.last_success_utc: datetime | None = None

    async def _async_update_data(self):
        try:
            result = await self.hass.async_add_executor_job(self._get_seneye_data)
            self.last_success_utc = datetime.now(timezone.utc)
            _LOGGER.debug("Seneye HID poll OK: %s", type(result).__name__)
            return result
        except Exception as err:
            _LOGGER.error("Seneye HID poll failed: %s", err)
            raise UpdateFailed(f"Error communicating with Seneye device: {err}") from err

    def _get_seneye_data(self):
        from pyseneye.sud import SUDevice, Action
        device = SUDevice()
        try:
            device.action(Action.ENTER_INTERACTIVE_MODE)
            return device.action(Action.SENSOR_READING)
        finally:
            device.close()


class SeneyeMqttCoordinator(DataUpdateCoordinator):
    """MQTT backend — push-based, no polling. Data arrives from seneye_mqtt_publisher."""

    def __init__(self, hass: HomeAssistant, prefix: str,
                 temp_offset: float, ph_offset: float, par_scale: float) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN)  # no update_interval — push only
        self.prefix = prefix.strip().rstrip("/")
        self.temp_offset = float(temp_offset)
        self.ph_offset = float(ph_offset)
        self.par_scale = float(par_scale)
        self.last_success_utc: datetime | None = None
        self.mqtt_online: bool | None = None  # None=unknown, True/False after first LWT
        self._unsub_state = None
        self._unsub_status = None

    async def async_subscribe(self) -> None:
        from homeassistant.components import mqtt
        self._unsub_state = await mqtt.async_subscribe(
            self.hass,
            f"{self.prefix}/state",
            self._on_state_message,
            qos=1,
        )
        self._unsub_status = await mqtt.async_subscribe(
            self.hass,
            f"{self.prefix}/status",
            self._on_status_message,
            qos=1,
        )
        _LOGGER.info(
            "Seneye MQTT subscribed to %s/state and %s/status",
            self.prefix, self.prefix,
        )

    @callback
    def _on_state_message(self, msg) -> None:
        try:
            payload = msg.payload if isinstance(msg.payload, str) else msg.payload.decode("utf-8")
            data = json.loads(payload)
            ns = types.SimpleNamespace(**data)
            self.last_success_utc = datetime.now(timezone.utc)
            self.async_set_updated_data(ns)
            _LOGGER.debug("Seneye MQTT state received: %s", data)
        except Exception as err:
            _LOGGER.error("Failed to parse Seneye MQTT message: %s", err)

    @callback
    def _on_status_message(self, msg) -> None:
        payload = msg.payload if isinstance(msg.payload, str) else msg.payload.decode("utf-8", errors="replace")
        self.mqtt_online = payload.strip() == "online"
        _LOGGER.debug("Seneye MQTT status: %s", payload.strip())

    def async_unsubscribe(self) -> None:
        if self._unsub_state:
            self._unsub_state()
            self._unsub_state = None
        if self._unsub_status:
            self._unsub_status()
            self._unsub_status = None
        _LOGGER.debug("Seneye MQTT unsubscribed")
