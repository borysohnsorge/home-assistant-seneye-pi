"""Config flow for the Seneye integration."""
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .const import (
    DOMAIN,
    CONF_BACKEND, BACKEND_HID, BACKEND_MQTT,
    CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX,
    CONF_UPDATE_INTERVAL_MIN, CONF_TEMP_OFFSET, CONF_PH_OFFSET, CONF_PAR_SCALE,
    DEFAULT_UPDATE_INTERVAL_MIN, DEFAULT_TEMP_OFFSET, DEFAULT_PH_OFFSET, DEFAULT_PAR_SCALE,
)


async def _mqtt_is_available(hass: HomeAssistant) -> bool:
    try:
        from homeassistant.components import mqtt
        return mqtt.async_is_connected(hass)
    except Exception:
        return False


class SeneyeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Seneye config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._backend: str = BACKEND_HID

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._backend = user_input[CONF_BACKEND]
            if self._backend == BACKEND_MQTT:
                return await self.async_step_mqtt()
            return self.async_create_entry(
                title="Seneye (HID)",
                data={CONF_BACKEND: BACKEND_HID},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_BACKEND, default=BACKEND_HID): SelectSelector(
                    SelectSelectorConfig(
                        options=[BACKEND_HID, BACKEND_MQTT],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    async def async_step_mqtt(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            if not await _mqtt_is_available(self.hass):
                errors["base"] = "mqtt_not_configured"
            else:
                prefix = user_input[CONF_MQTT_PREFIX].strip().rstrip("/")
                return self.async_create_entry(
                    title=f"Seneye (MQTT: {prefix})",
                    data={CONF_BACKEND: BACKEND_MQTT, CONF_MQTT_PREFIX: prefix},
                )

        return self.async_show_form(
            step_id="mqtt",
            data_schema=vol.Schema({
                vol.Required(CONF_MQTT_PREFIX, default=DEFAULT_MQTT_PREFIX): TextSelector(),
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SeneyeOptionsFlow()


class SeneyeOptionsFlow(OptionsFlow):
    """Seneye options flow."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        backend = self.config_entry.data.get(CONF_BACKEND, BACKEND_HID)
        opts = self.config_entry.options

        schema_fields: dict = {}

        if backend == BACKEND_HID:
            schema_fields[vol.Optional(
                CONF_UPDATE_INTERVAL_MIN,
                default=int(opts.get(CONF_UPDATE_INTERVAL_MIN, DEFAULT_UPDATE_INTERVAL_MIN)),
            )] = NumberSelector(NumberSelectorConfig(min=1, max=60, step=1, mode=NumberSelectorMode.BOX))

        schema_fields[vol.Optional(
            CONF_TEMP_OFFSET,
            default=float(opts.get(CONF_TEMP_OFFSET, DEFAULT_TEMP_OFFSET)),
        )] = NumberSelector(NumberSelectorConfig(min=-5.0, max=5.0, step=0.1, mode=NumberSelectorMode.BOX))

        schema_fields[vol.Optional(
            CONF_PH_OFFSET,
            default=float(opts.get(CONF_PH_OFFSET, DEFAULT_PH_OFFSET)),
        )] = NumberSelector(NumberSelectorConfig(min=-2.0, max=2.0, step=0.01, mode=NumberSelectorMode.BOX))

        schema_fields[vol.Optional(
            CONF_PAR_SCALE,
            default=float(opts.get(CONF_PAR_SCALE, DEFAULT_PAR_SCALE)),
        )] = NumberSelector(NumberSelectorConfig(min=0.1, max=10.0, step=0.1, mode=NumberSelectorMode.BOX))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_fields),
        )
