import unittest
from unittest.mock import MagicMock, patch

from config import app_constants
from managers.settings_manager import SettingsManager


class TestSettingsManagerTypeSafety(unittest.TestCase):
    @patch("managers.settings_manager.QSettings")
    def test_load_with_type_mismatches(self, mock_q_settings_class):
        mock_q_settings = MagicMock()
        mock_q_settings_class.return_value = mock_q_settings

        # Mock stored values that have mismatched or legacy types
        stored_data = {
            "remember_settings": "true",
            "hud_win_x": "not_an_int",  # Should fallback to default (100)
            "hud_win_y": 250,  # Valid int
            "last_used_folder": 12345,  # Stored as int instead of str -> coerced to string
            "recent_items_history": "single_path.jpg",  # Stored as str instead of list
            "ratio_preference": "1:1 Square",  # Legacy string literal -> should normalize to CropRatioMode.SQUARE_1_1
            "engine_preference": app_constants.EngineMode.PIXEL_PERFECT,  # IntEnum
            "snap_preference": "Ghosting",  # Legacy string literal -> should normalize to SnapMode.GHOSTING
        }

        mock_q_settings.contains.side_effect = lambda key: key in stored_data
        mock_q_settings.value.side_effect = lambda key: stored_data.get(key)

        manager = SettingsManager("TestOrg", "TestApp")
        settings = manager.load()

        self.assertIsInstance(settings.remember_settings, bool)
        self.assertTrue(settings.remember_settings)

        self.assertIsInstance(settings.hud_win_x, int)
        self.assertEqual(settings.hud_win_x, 100)  # Fallback default

        self.assertIsInstance(settings.hud_win_y, int)
        self.assertEqual(settings.hud_win_y, 250)

        self.assertIsInstance(settings.last_used_folder, str)
        self.assertEqual(settings.last_used_folder, "12345")

        self.assertIsInstance(settings.recent_items_history, list)
        self.assertEqual(settings.recent_items_history, ["single_path.jpg"])

        self.assertEqual(
            settings.ratio_preference, app_constants.CropRatioMode.SQUARE_1_1
        )
        self.assertEqual(
            settings.engine_preference, app_constants.EngineMode.PIXEL_PERFECT
        )
        self.assertEqual(settings.snap_preference, app_constants.SnapMode.GHOSTING)


if __name__ == "__main__":
    unittest.main()
