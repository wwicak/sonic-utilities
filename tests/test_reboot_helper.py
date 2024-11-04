import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

sys.modules['sonic_platform'] = MagicMock()
import scripts.reboot_helper  # noqa: E402


class TestRebootHelper(unittest.TestCase):

    @patch(
            'scripts.reboot_helper.is_smartswitch',
            MagicMock(return_value=False)
            )
    def test_get_all_dpus_not_smartswitch(self):
        dpu_list = scripts.reboot_helper.get_all_dpus()
        self.assertEqual(dpu_list, [])

    @patch(
        'os.path.join', MagicMock(return_value="/mock/path/platform.json")
        )
    @patch(
        'builtins.open', new_callable=mock_open,
        read_data='{"DPUS": {"DPU1": {}, "DPU2": {}}}'
        )
    @patch(
        'scripts.reboot_helper.device_info.get_platform_info',
        MagicMock(return_value={'platform': 'mock_platform'})
        )
    @patch(
        'scripts.reboot_helper.is_smartswitch', MagicMock(return_value=True)
        )
    def test_get_all_dpus_valid_json(self, mock_is_smartswitch):
        dpu_list = scripts.reboot_helper.get_all_dpus()
        self.assertEqual(dpu_list, ["DPU1", "DPU2"])

    @patch(
        'scripts.reboot_helper.sonic_platform.platform.Platform.get_chassis'
        )
    def test_load_platform_chassis_success(self, mock_get_chassis):
        mock_get_chassis.return_value = MagicMock()
        result = scripts.reboot_helper.load_platform_chassis()
        self.assertTrue(result)

    @patch(
        'scripts.reboot_helper.load_platform_chassis',
        MagicMock(return_value=False)
        )
    def test_reboot_module_chassis_fail(self):
        result = scripts.reboot_helper.reboot_module("DPU1")
        self.assertFalse(result)

    @patch(
        'scripts.reboot_helper.load_platform_chassis',
        MagicMock(return_value=True)
        )
    @patch(
        'scripts.reboot_helper.is_smartswitch', MagicMock(return_value=False)
        )
    def test_reboot_module_not_smartswitch(self):
        result = scripts.reboot_helper.reboot_module("DPU1")
        self.assertFalse(result)

    @patch(
        'scripts.reboot_helper.get_all_dpus', MagicMock(return_value=["DPU1"])
        )
    @patch(
        'scripts.reboot_helper.load_platform_chassis',
        MagicMock(return_value=True)
        )
    @patch(
        'scripts.reboot_helper.is_smartswitch', MagicMock(return_value=True)
        )
    def test_reboot_module_not_found(self):
        result = scripts.reboot_helper.reboot_module("DPU2")
        self.assertFalse(result)

    @patch(
        'scripts.reboot_helper.get_all_dpus', MagicMock(return_value=["DPU1"])
        )
    @patch(
        'scripts.reboot_helper.load_platform_chassis',
        MagicMock(return_value=True)
        )
    @patch(
        'scripts.reboot_helper.is_smartswitch', MagicMock(return_value=True)
        )
    @patch(
        'scripts.reboot_helper.platform_chassis.reboot',
        MagicMock(return_value=True)
        )
    def test_reboot_module_success(self):
        result = scripts.reboot_helper.reboot_module("DPU1")
        self.assertTrue(result)

    @patch(
        'scripts.reboot_helper.load_platform_chassis',
        MagicMock(return_value=False)
        )
    def test_is_dpu_load_platform_chassis_fail(self):
        result = scripts.reboot_helper.is_dpu()
        self.assertFalse(result)

    @patch(
        'scripts.reboot_helper.load_platform_chassis',
        MagicMock(return_value=True)
        )
    @patch(
        'scripts.reboot_helper.is_smartswitch', MagicMock(return_value=False)
        )
    def test_is_dpu_not_smartswitch(self):
        result = scripts.reboot_helper.is_dpu()
        self.assertFalse(result)

    @patch(
        'os.path.join', MagicMock(return_value="/mock/path/platform.json")
        )
    @patch(
        'builtins.open', new_callable=mock_open,
        read_data='{".DPU": {}}'
        )
    @patch(
        'scripts.reboot_helper.device_info.get_platform_info',
        MagicMock(return_value={'platform': 'mock_platform'})
        )
    @patch('scripts.reboot_helper.load_platform_chassis')
    @patch('scripts.reboot_helper.is_smartswitch')
    def test_is_dpu_found(self, mock_is_smartswitch,
                          mock_load_platform_chassis,
                          mock_get_platform_info):
        mock_is_smartswitch.return_value = True
        mock_load_platform_chassis.return_value = True
        result = scripts.reboot_helper.is_dpu()
        self.assertTrue(result)

    @patch(
        'os.path.join', MagicMock(return_value="/mock/path/platform.json")
        )
    @patch(
        'builtins.open', new_callable=mock_open,
        read_data='{}'
        )
    @patch(
        'scripts.reboot_helper.device_info.get_platform_info',
        MagicMock(return_value={'platform': 'mock_platform'})
        )
    @patch(
        'scripts.reboot_helper.load_platform_chassis',
        MagicMock(return_value=True)
        )
    @patch(
        'scripts.reboot_helper.is_smartswitch', MagicMock(return_value=True)
        )
    def test_is_dpu_not_found(self, mock_is_smartswitch):
        result = scripts.reboot_helper.is_dpu()
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
