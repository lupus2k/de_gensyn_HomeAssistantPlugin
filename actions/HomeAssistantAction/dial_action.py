"""
The module for the Home Assistant Dial action that is loaded in StreamController.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from src.backend.DeckManagement.InputIdentifier import Input, InputEvent
from de_gensyn_HomeAssistantPlugin.actions.HomeAssistantAction.home_asistant_action import HomeAssistantAction

# Constants for settings keys
SETTING_DIAL_ENTITY_ID = "dial_entity_id"
SETTING_DIAL_STEP_SIZE = "dial_step_size"
SETTING_DIAL_TURN_SERVICE = "dial_turn_service"
SETTING_DIAL_PRESS_SERVICE = "dial_press_service"

class DialAction(HomeAssistantAction):
    """
    Dial Action to be loaded by StreamController.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize settings attributes
        self.dial_entity_id: str = ""
        self.dial_step_size: int = 1
        self.dial_turn_service: str = ""
        self.dial_press_service: str = ""
        
        # Initialize UI element attributes
        self.dial_entity_id_row: Adw.EntryRow | None = None
        self.dial_step_size_row: Adw.SpinRow | None = None
        self.dial_turn_service_row: Adw.EntryRow | None = None
        self.dial_press_service_row: Adw.EntryRow | None = None
        
        self._load_dial_settings()

    def _load_dial_settings(self) -> None:
        """
        Load dial-specific settings.
        """
        settings = self.get_settings()
        self.dial_entity_id = settings.get(SETTING_DIAL_ENTITY_ID, "")
        self.dial_step_size = settings.get(SETTING_DIAL_STEP_SIZE, 1)
        self.dial_turn_service = settings.get(SETTING_DIAL_TURN_SERVICE, "")
        self.dial_press_service = settings.get(SETTING_DIAL_PRESS_SERVICE, "")

    def _save_dial_settings(self) -> None:
        """
        Save dial-specific settings.
        """
        settings = self.get_settings()
        settings[SETTING_DIAL_ENTITY_ID] = self.dial_entity_id
        settings[SETTING_DIAL_STEP_SIZE] = self.dial_step_size
        settings[SETTING_DIAL_TURN_SERVICE] = self.dial_turn_service
        settings[SETTING_DIAL_PRESS_SERVICE] = self.dial_press_service
        self.set_settings(settings)

    def event_callback(self, event: InputEvent, data: dict) -> None:
        """
        Callback for dial events.
        """
        if not self.dial_entity_id:
            print("DialAction: No entity ID configured. Cannot perform action.")
            return

        if event == Input.Dial.Events.DOWN:
            if self.dial_press_service:
                print(f"DialAction: Calling dial press service: {self.dial_press_service} on {self.dial_entity_id}")
                try:
                    # Assuming service format is "domain.service_name", e.g., "light.toggle"
                    # The backend's call_service likely takes entity_id, service_name, and parameters.
                    # The domain is often implicit via the entity_id for HA services.
                    _domain, service_name = self.dial_press_service.split('.', 1)
                    
                    service_data = {"entity_id": self.dial_entity_id}
                    
                    # self.plugin_base.backend.call_service(entity_id, service_name, service_data)
                    # The HomeAssistantAction on_key_down uses:
                    # self.plugin_base.backend.call_service(entity, service, parameters)
                    # where entity is dial_entity_id, service is service_name.
                    self.plugin_base.backend.call_service(self.dial_entity_id, service_name, service_data)
                    print(f"DialAction: Service call {self.dial_press_service} for {self.dial_entity_id} successful.")
                except ValueError:
                    print(f"DialAction: Invalid service format for dial_press_service: {self.dial_press_service}. Expected 'domain.service_name'.")
                except Exception as e:
                    print(f"DialAction: Error calling service {self.dial_press_service} for {self.dial_entity_id}: {e}")
            else:
                print("DialAction: Dial pressed, but no press service configured.")

        elif event == Input.Dial.Events.TURN_CW:
            if self.dial_turn_service:
                try:
                    _domain, service_name = self.dial_turn_service.split('.', 1)
                    step = self.dial_step_size
                    service_data = {
                        "entity_id": self.dial_entity_id, # Including for services that might need it in data
                        "brightness_step_pct": step
                    }
                    print(f"DialAction: Dial CW, calling service '{service_name}' on '{self.dial_entity_id}' with data: {service_data}")
                    self.plugin_base.backend.call_service(self.dial_entity_id, service_name, service_data)
                    print(f"DialAction: Service call {self.dial_turn_service} for CW turn successful.")
                except ValueError:
                    print(f"DialAction: Invalid service format for dial_turn_service: {self.dial_turn_service}. Expected 'domain.service_name'.")
                except Exception as e:
                    print(f"DialAction: Error calling service {self.dial_turn_service} for CW turn on {self.dial_entity_id}: {e}")
            else:
                print("DialAction: Dial turned clockwise, but no turn service configured.")
        
        elif event == Input.Dial.Events.TURN_CCW:
            if self.dial_turn_service:
                try:
                    _domain, service_name = self.dial_turn_service.split('.', 1)
                    step = -self.dial_step_size 
                    service_data = {
                        "entity_id": self.dial_entity_id, # Including for services that might need it in data
                        "brightness_step_pct": step
                    }
                    print(f"DialAction: Dial CCW, calling service '{service_name}' on '{self.dial_entity_id}' with data: {service_data}")
                    self.plugin_base.backend.call_service(self.dial_entity_id, service_name, service_data)
                    print(f"DialAction: Service call {self.dial_turn_service} for CCW turn successful.")
                except ValueError:
                    print(f"DialAction: Invalid service format for dial_turn_service: {self.dial_turn_service}. Expected 'domain.service_name'.")
                except Exception as e:
                    print(f"DialAction: Error calling service {self.dial_turn_service} for CCW turn on {self.dial_entity_id}: {e}")
            else:
                print("DialAction: Dial turned counter-clockwise, but no turn service configured.")
        
        else:
            super().event_callback(event, data)

    def get_config_rows(self) -> list:
        """
        Get the configuration rows for the Dial action.
        """
        config_rows: list = super().get_config_rows()

        # Dial Settings Group
        # Note: The title "Dial Settings" for the PreferencesGroup itself is not localized here
        # as it's a structural element title, not a direct user-facing label for a specific field.
        # If this also needs localization, a key would be needed, e.g., "actions.dial_action.group.title"
        dial_settings_group = Adw.PreferencesGroup(title="Dial Settings") 
        
        lm = self.plugin_base.locale_manager
        
        dial_expander_row = Adw.ExpanderRow(title=lm.get("actions.dial_action.config.title"))
        dial_settings_group.add(dial_expander_row)

        # Entity ID Row
        self.dial_entity_id_row = Adw.EntryRow(title=lm.get("actions.dial_action.config.entity_id.title"))
        self.dial_entity_id_row.set_text(self.dial_entity_id)
        self.dial_entity_id_row.connect("notify::text", self._on_dial_entity_id_changed)
        dial_expander_row.add_row(self.dial_entity_id_row)

        # Step Size Row
        step_size_adjustment = Gtk.Adjustment(value=self.dial_step_size, lower=1, upper=100, step_increment=1)
        self.dial_step_size_row = Adw.SpinRow(
            title=lm.get("actions.dial_action.config.step_size.title"),
            adjustment=step_size_adjustment
        )
        self.dial_step_size_row.get_adjustment().connect("value-changed", self._on_dial_step_size_changed)
        dial_expander_row.add_row(self.dial_step_size_row)

        # Dial Turn Service Row
        self.dial_turn_service_row = Adw.EntryRow(title=lm.get("actions.dial_action.config.turn_service.title"))
        self.dial_turn_service_row.set_placeholder_text(lm.get("actions.dial_action.config.turn_service.placeholder"))
        self.dial_turn_service_row.set_text(self.dial_turn_service)
        self.dial_turn_service_row.connect("notify::text", self._on_dial_turn_service_changed)
        dial_expander_row.add_row(self.dial_turn_service_row)

        # Dial Press Service Row
        self.dial_press_service_row = Adw.EntryRow(title=lm.get("actions.dial_action.config.press_service.title"))
        self.dial_press_service_row.set_placeholder_text(lm.get("actions.dial_action.config.press_service.placeholder"))
        self.dial_press_service_row.set_text(self.dial_press_service)
        self.dial_press_service_row.connect("notify::text", self._on_dial_press_service_changed)
        dial_expander_row.add_row(self.dial_press_service_row)
        
        config_rows.append(dial_settings_group)

        return config_rows

    def _on_dial_entity_id_changed(self, entry_row: Adw.EntryRow, _param) -> None:
        self.dial_entity_id = entry_row.get_text()
        self._save_dial_settings()

    def _on_dial_step_size_changed(self, adjustment: Gtk.Adjustment) -> None:
        self.dial_step_size = int(adjustment.get_value())
        self._save_dial_settings()

    def _on_dial_turn_service_changed(self, entry_row: Adw.EntryRow, _param) -> None:
        self.dial_turn_service = entry_row.get_text()
        self._save_dial_settings()

    def _on_dial_press_service_changed(self, entry_row: Adw.EntryRow, _param) -> None:
        self.dial_press_service = entry_row.get_text()
        self._save_dial_settings()
