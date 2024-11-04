# tests/test_reboot_helper.py

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

sys.modules['sonic_platform'] = MagicMock()
import scripts.reboot_helper  # noqa: E402


@pytest.fixture
def mock_load_platform_chassis():
    with patch('scripts.reboot_helper.load_platform_chassis', return_value=True) as mock:
        yield mock


@pytest.fixture
def mock_is_smartswitch():
    with patch('scripts.reboot_helper.is_smartswitch', return_value=True) as mock:
        yield mock


@pytest.fixture
def mock_get_platform_info():
    with patch('scripts.reboot_helper.device_info.get_platform_info') as mock:
        yield mock


@pytest.fixture
def mock_open_file():
    return mock_open()


@pytest.fixture
def mock_platform_chassis():
    with patch('scripts.reboot_helper.platform_chassis') as mock:
        yield mock


@pytest.fixture
def mock_platform():
    with patch('scripts.reboot_helper.sonic_platform.platform.Platform') as mock:
        yield mock


def test_get_all_dpus_not_smartswitch(mock_is_smartswitch):
    mock_is_smartswitch.return_value = False
    dpu_list = scripts.reboot_helper.get_all_dpus()
    assert dpu_list == []


def test_get_all_dpus_invalid_platform_info(mock_is_smartswitch, mock_get_platform_info):
    mock_is_smartswitch.return_value = True
    mock_get_platform_info.return_value = {'platform': None}
    dpu_list = scripts.reboot_helper.get_all_dpus()
    assert dpu_list == []


def test_get_all_dpus_file_not_found(mock_open_file):
    with patch('builtins.open', side_effect=FileNotFoundError):
        dpu_list = scripts.reboot_helper.get_all_dpus()
        assert dpu_list == []


def test_get_all_dpus_malformed_json(mock_is_smartswitch, mock_get_platform_info, mock_open_file):
    mock_is_smartswitch.return_value = True
    mock_get_platform_info.return_value = {'platform': 'mock_platform'}

    with patch('builtins.open', mock_open(read_data='Invalid JSON')):
        dpu_list = scripts.reboot_helper.get_all_dpus()
        assert dpu_list == []


def test_get_all_dpus_valid_json(mock_is_smartswitch, mock_get_platform_info, mock_open_file):
    mock_is_smartswitch.return_value = True
    mock_get_platform_info.return_value = {'platform': 'mock_platform'}

    with patch('builtins.open', mock_open(read_data='{"DPUS": {"DPU1": {}, "DPU2": {}}}')):
        dpu_list = scripts.reboot_helper.get_all_dpus()
        assert dpu_list == ["DPU1", "DPU2"]


def test_load_platform_chassis_success(mock_platform_chassis):
    mock_platform_chassis.get_chassis.return_value = MagicMock()
    result = scripts.reboot_helper.load_platform_chassis()
    assert result


def test_load_platform_chassis_exception(mock_platform):
    mock_platform.side_effect = RuntimeError
    result = scripts.reboot_helper.load_platform_chassis()
    assert not result


def test_reboot_module_chassis_fail(mock_load_platform_chassis):
    mock_load_platform_chassis.return_value = False
    result = scripts.reboot_helper.reboot_module("DPU1")
    assert not result


def test_reboot_module_not_smartswitch(mock_load_platform_chassis):
    with patch('scripts.reboot_helper.is_smartswitch', return_value=False):
        result = scripts.reboot_helper.reboot_module("DPU1")
        assert not result


def test_reboot_module_not_found(mock_load_platform_chassis, mock_get_platform_info):
    mock_get_platform_info.return_value = {'platform': 'mock_platform'}
    with patch('scripts.reboot_helper.get_all_dpus', return_value=["DPU1"]):
        result = scripts.reboot_helper.reboot_module("DPU2")
        assert not result


def test_reboot_module_not_implemented(mock_load_platform_chassis, mock_is_smartswitch,
                                       mock_get_platform_info, mock_platform_chassis):
    mock_get_platform_info.return_value = {'platform': 'mock_platform'}
    mock_platform_chassis.reboot.side_effect = NotImplementedError
    with patch('scripts.reboot_helper.get_all_dpus', return_value=["DPU1"]):
        with pytest.raises(RuntimeError):
            scripts.reboot_helper.reboot_module("DPU1")


def test_reboot_module_empty_dpu_list(mock_load_platform_chassis):
    with patch('scripts.reboot_helper.get_all_dpus', return_value=[]):
        result = scripts.reboot_helper.reboot_module("DPU1")
        assert not result


def test_reboot_module_success(mock_load_platform_chassis, mock_is_smartswitch,
                               mock_get_platform_info, mock_platform_chassis):
    mock_get_platform_info.return_value = {'platform': 'mock_platform'}
    with patch('scripts.reboot_helper.get_all_dpus', return_value=["DPU1"]):
        mock_platform_chassis.reboot.return_value = True
        result = scripts.reboot_helper.reboot_module("DPU1")
        assert result


def test_is_dpu_load_platform_chassis_fail(mock_load_platform_chassis):
    mock_load_platform_chassis.return_value = False
    result = scripts.reboot_helper.is_dpu()
    assert not result


def test_is_dpu_not_smartswitch(mock_load_platform_chassis):
    mock_load_platform_chassis.return_value = True
    with patch('scripts.reboot_helper.is_smartswitch', return_value=False):
        result = scripts.reboot_helper.is_dpu()
        assert not result


def test_is_dpu_found(mock_is_smartswitch, mock_load_platform_chassis, mock_get_platform_info, mock_open_file):
    mock_is_smartswitch.return_value = True
    mock_load_platform_chassis.return_value = True
    mock_get_platform_info.return_value = {'platform': 'mock_platform'}

    with patch('builtins.open', mock_open(read_data='{".DPU": {}}')):
        result = scripts.reboot_helper.is_dpu()
        assert result


def test_is_dpu_not_found(mock_is_smartswitch, mock_load_platform_chassis, mock_get_platform_info, mock_open_file):
    mock_is_smartswitch.return_value = True
    mock_load_platform_chassis.return_value = True
    mock_get_platform_info.return_value = {'platform': 'mock_platform'}

    with patch('builtins.open', mock_open(read_data='{}')):
        result = scripts.reboot_helper.is_dpu()
        assert not result


def test_pci_detach_module_chassis_fail(mock_load_platform_chassis):
    mock_load_platform_chassis.return_value = False
    result = scripts.reboot_helper.pci_detach_module("DPU1")
    assert not result


def test_pci_detach_module_not_smartswitch(mock_load_platform_chassis):
    with patch('scripts.reboot_helper.is_smartswitch', return_value=False):
        result = scripts.reboot_helper.pci_detach_module("DPU1")
        assert not result


def test_pci_detach_module_not_found(mock_load_platform_chassis, mock_get_platform_info):
    mock_get_platform_info.return_value = {'platform': 'mock_platform'}
    with patch('scripts.reboot_helper.get_all_dpus', return_value=["DPU1"]):
        result = scripts.reboot_helper.pci_detach_module("DPU2")
        assert not result


def test_pci_detach_module_not_implemented(mock_load_platform_chassis, mock_is_smartswitch,
                                           mock_get_platform_info, mock_platform_chassis):
    mock_get_platform_info.return_value = {'platform': 'mock_platform'}
    mock_platform_chassis.pci_detach.side_effect = NotImplementedError
    with patch('scripts.reboot_helper.get_all_dpus', return_value=["DPU1"]):
        with pytest.raises(RuntimeError):
            scripts.reboot_helper.pci_detach_module("DPU1")


def test_pci_detach_module_empty_dpu_list(mock_load_platform_chassis):
    with patch('scripts.reboot_helper.get_all_dpus', return_value=[]):
        result = scripts.reboot_helper.pci_detach_module("DPU1")
        assert not result


def test_pci_detach_module_success(mock_load_platform_chassis, mock_is_smartswitch,
                                   mock_get_platform_info, mock_platform_chassis):
    mock_get_platform_info.return_value = {'platform': 'mock_platform'}
    with patch('scripts.reboot_helper.get_all_dpus', return_value=["DPU1"]):
        mock_platform_chassis.reboot.return_value = True
        result = scripts.reboot_helper.pci_detach_module("DPU1")
        assert result


def test_main_reboot_command_success(monkeypatch):
    # Simulate command-line arguments for reboot
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'reboot', 'DPU1'])

    # Mock dependencies
    with patch('scripts.reboot_helper.reboot_module', return_value=True) as mock_reboot_module, \
         patch('sys.exit') as mock_exit:

        scripts.reboot_helper.main()

        # Check that reboot_module was called
        mock_reboot_module.assert_called_once_with('DPU1')
        mock_exit.assert_not_called()


def test_main_reboot_command_fail(monkeypatch):
    # Simulate command-line arguments for reboot
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'reboot', 'DPU1'])

    # Mock dependencies
    with patch('scripts.reboot_helper.reboot_module', return_value=False), \
         patch('sys.exit') as mock_exit:

        scripts.reboot_helper.main()

        # Check that sys.exit was called with EXIT_FAIL
        mock_exit.assert_called_once_with(scripts.reboot_helper.EXIT_FAIL)


def test_main_is_dpu_command_true(monkeypatch):
    # Simulate command-line arguments for is_dpu
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'is_dpu'])

    # Mock is_dpu to return True
    with patch('scripts.reboot_helper.is_dpu', return_value=True), \
         patch('builtins.print') as mock_print, \
         patch('sys.exit') as mock_exit, \
         patch('builtins.print') as mock_print:
        scripts.reboot_helper.main()

        # Check that the message was printed
        mock_print.assert_called_with("Script is running on DPU module")
        mock_exit.assert_not_called()


def test_main_is_dpu_command_false(monkeypatch):
    # Simulate command-line arguments for is_dpu
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'is_dpu'])

    # Mock is_dpu to return False
    with patch('scripts.reboot_helper.is_dpu', return_value=False), \
         patch('sys.exit') as mock_exit, \
         patch('builtins.print') as mock_print:
        scripts.reboot_helper.main()

        # Check that sys.exit was called with EXIT_FAIL
        mock_print.assert_not_called()
        mock_exit.assert_called_once_with(scripts.reboot_helper.EXIT_FAIL)


def test_main_pci_detach_command_success(monkeypatch):
    # Simulate command-line arguments for reboot
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'pci_detach', 'DPU1'])

    # Mock dependencies
    with patch('scripts.reboot_helper.pci_detach_module', return_value=True) as mock_reboot_module, \
         patch('sys.exit') as mock_exit:

        scripts.reboot_helper.main()

        # Check that pci_detach_module was called
        mock_reboot_module.assert_called_once_with('DPU1')
        mock_exit.assert_not_called()


def test_main_pci_detach_command_fail(monkeypatch):
    # Simulate command-line arguments for reboot
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'pci_detach', 'DPU1'])

    # Mock dependencies
    with patch('scripts.reboot_helper.pci_detach_module', return_value=False), \
         patch('sys.exit') as mock_exit:

        scripts.reboot_helper.main()

        # Check that sys.exit was called with EXIT_FAIL
        mock_exit.assert_called_once_with(scripts.reboot_helper.EXIT_FAIL)


def test_main_unknown_command(monkeypatch):
    # Simulate an unknown command
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'unknown', 'DPU1'])

    # Mock sys.exit and capture print output
    with patch('sys.exit') as mock_exit, patch('builtins.print') as mock_print:
        scripts.reboot_helper.main()

        # Check that the unknown command message was printed
        mock_print.assert_called_with("Unknown command: unknown")
        mock_exit.assert_called_once_with(scripts.reboot_helper.EXIT_FAIL)
