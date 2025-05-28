import unittest
from unittest.mock import Mock, patch, call
from actions.HomeAssistantAction.dial_action import DialAction, SETTING_DIAL_ENTITY_ID, SETTING_DIAL_STEP_SIZE, SETTING_DIAL_TURN_SERVICE, SETTING_DIAL_PRESS_SERVICE
from src.backend.DeckManagement.InputIdentifier import Input, InputEvent

class TestDialAction(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        self.mock_plugin_base = Mock()
        self.mock_plugin_base.locale_manager = Mock()
        self.mock_plugin_base.locale_manager.get.return_value = "mocked string"
        
        self.mock_plugin_base.backend = Mock()
        self.mock_plugin_base.backend.call_service = Mock()

        # Mock settings methods for DialAction's __init__ and subsequent operations
        # _load_dial_settings in __init__ calls self.get_settings()
        self.mock_get_settings = Mock(return_value={}) 
        self.mock_set_settings = Mock()

        # Patch get_settings and set_settings on the DialAction class itself before instantiation
        # This is tricky because DialAction inherits them. We need to patch where they are looked up.
        # A common way is to patch them on the instance *after* super().__init__ if they are not class/static methods
        # However, _load_dial_settings is called in DialAction's __init__.
        # Let's assume HomeAssistantAction (parent) provides default get/set_settings if not overridden by plugin_base
        # For simplicity in a unit test, we can patch them directly on the instance or ensure plugin_base has them.

        # Let's simulate that plugin_base provides these, as ActionBase expects them.
        self.mock_plugin_base.get_settings = self.mock_get_settings
        self.mock_plugin_base.set_settings = self.mock_set_settings
        
        # Instantiate DialAction
        # The DialAction's __init__ calls self._load_dial_settings(), which calls self.get_settings().
        # The base ActionBase.__init__ calls self.plugin_base.get_settings(self.action_id)
        # So, we need self.mock_plugin_base.get_settings to be ready.
        # It seems ActionBase uses plugin_base.get_settings(action_id) and plugin_base.set_settings(action_id, settings)
        # Let's adjust the mock for this.
        
        self.mock_plugin_base.get_settings.return_value = {} # For the call in ActionBase init
        
        # For the call in DialAction._load_dial_settings -> self.get_settings()
        # This refers to the method on the action instance itself.
        # We need to patch 'actions.HomeAssistantAction.dial_action.DialAction.get_settings'
        # and 'actions.HomeAssistantAction.dial_action.DialAction.set_settings'
        
        # It's simpler if we ensure the instance's get_settings returns what we want for _load_dial_settings
        # The initial settings load in DialAction's __init__ uses self.get_settings.
        # We'll patch it on the class temporarily for instantiation.
        
        with patch.object(DialAction, 'get_settings', return_value={}) as mock_instance_get_settings, \
             patch.object(DialAction, 'set_settings', return_value=None) as mock_instance_set_settings:
            self.action = DialAction(plugin_base=self.mock_plugin_base, action_id="test_dial_action")
            # Store the mock if needed for assertions on set_settings called by the action itself
            self.action_get_settings_mock = mock_instance_get_settings
            self.action_set_settings_mock = mock_instance_set_settings


    def test_initialization_default_settings(self):
        """Test that DialAction initializes with default settings."""
        # This test relies on the __init__ calling _load_dial_settings,
        # and _load_dial_settings using self.get_settings() which was mocked to return {}
        self.assertEqual(self.action.dial_entity_id, "")
        self.assertEqual(self.action.dial_step_size, 1)
        self.assertEqual(self.action.dial_turn_service, "")
        self.assertEqual(self.action.dial_press_service, "")

    def test_event_callback_dial_press_valid(self):
        """Test dial press with valid entity and service calls backend."""
        # Override the initial settings load if necessary, or set directly
        self.action.dial_entity_id = "light.living_room"
        self.action.dial_press_service = "light.toggle"
        # Ensure get_settings reflects these if _save_dial_settings was called and then _load_dial_settings
        # For this test, direct attribute setting is fine as we are testing event_callback's use of them.

        self.action.event_callback(Input.Dial.Events.DOWN, {})
        
        self.mock_plugin_base.backend.call_service.assert_called_once_with(
            "light.living_room", "toggle", {"entity_id": "light.living_room"}
        )

    def test_event_callback_dial_press_no_service(self):
        """Test dial press does not call backend if no service is configured."""
        self.action.dial_entity_id = "light.living_room"
        self.action.dial_press_service = "" # No service

        self.action.event_callback(Input.Dial.Events.DOWN, {})
        
        self.mock_plugin_base.backend.call_service.assert_not_called()

    def test_event_callback_dial_press_no_entity_id(self):
        """Test dial press does not call backend if no entity_id is configured."""
        self.action.dial_entity_id = "" # No entity
        self.action.dial_press_service = "light.toggle"

        self.action.event_callback(Input.Dial.Events.DOWN, {})
        
        self.mock_plugin_base.backend.call_service.assert_not_called()

    def test_event_callback_dial_turn_cw_valid(self):
        """Test dial turn CW with valid entity and service calls backend."""
        self.action.dial_entity_id = "light.office"
        self.action.dial_turn_service = "light.turn_on" # Example service
        self.action.dial_step_size = 10

        self.action.event_callback(Input.Dial.Events.TURN_CW, {})
        
        self.mock_plugin_base.backend.call_service.assert_called_once_with(
            "light.office", "turn_on", {"entity_id": "light.office", "brightness_step_pct": 10}
        )

    def test_event_callback_dial_turn_ccw_valid(self):
        """Test dial turn CCW with valid entity and service calls backend."""
        self.action.dial_entity_id = "light.office"
        self.action.dial_turn_service = "light.turn_on" # Example service
        self.action.dial_step_size = 5

        self.action.event_callback(Input.Dial.Events.TURN_CCW, {})
        
        self.mock_plugin_base.backend.call_service.assert_called_once_with(
            "light.office", "turn_on", {"entity_id": "light.office", "brightness_step_pct": -5}
        )

    def test_event_callback_dial_turn_no_service(self):
        """Test dial turn does not call backend if no turn service is configured."""
        self.action.dial_entity_id = "light.office"
        self.action.dial_turn_service = "" # No service
        self.action.dial_step_size = 10

        self.action.event_callback(Input.Dial.Events.TURN_CW, {})
        
        self.mock_plugin_base.backend.call_service.assert_not_called()

    def test_event_callback_dial_turn_no_entity_id(self):
        """Test dial turn does not call backend if no entity_id is configured."""
        self.action.dial_entity_id = "" # No entity
        self.action.dial_turn_service = "light.turn_on"
        self.action.dial_step_size = 10
        
        self.action.event_callback(Input.Dial.Events.TURN_CW, {})
        
        self.mock_plugin_base.backend.call_service.assert_not_called()

    def test_event_callback_dial_turn_invalid_service_format(self):
        """Test dial turn does not call backend if service format is invalid."""
        self.action.dial_entity_id = "light.office"
        self.action.dial_turn_service = "invalidserviceformat" # Invalid format
        self.action.dial_step_size = 10

        self.action.event_callback(Input.Dial.Events.TURN_CW, {})
        
        self.mock_plugin_base.backend.call_service.assert_not_called()

if __name__ == '__main__':
    unittest.main()
