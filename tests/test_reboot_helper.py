# tests/test_reboot_helper.py
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

sys.modules['sonic_platform'] = MagicMock()

sys.path.append("scripts")
import reboot_helper  # noqa: E402


@pytest.fixture
def mock_load_platform_chassis():
    with patch('reboot_helper.load_platform_chassis', return_value=True) as mock:
        yield mock


@pytest.fixture
def mock_load_and_verify():
    with patch('reboot_helper.load_and_verify', return_value=True) as mock:
        yield mock


@pytest.fixture
def mock_is_smartswitch():
    with patch('reboot_helper.is_smartswitch', return_value=True) as mock:
        yield mock


@pytest.fixture
def mock_open_file():
    return mock_open()


@pytest.fixture
def mock_platform_chassis():
    with patch('reboot_helper.platform_chassis') as mock:
        yield mock


@pytest.fixture
def mock_platform():
    with patch('reboot_helper.sonic_platform.platform.Platform') as mock:
        yield mock


@pytest.fixture
def mock_get_dpu_list():
    with patch('reboot_helper.get_dpu_list', return_value=["dpu1"]) as mock:
        yield mock


def test_load_platform_chassis_success(mock_platform_chassis):
    mock_platform_chassis.get_chassis.return_value = MagicMock()
    result = reboot_helper.load_platform_chassis()
    assert result


def test_load_platform_chassis_exception(mock_platform):
    mock_platform.side_effect = RuntimeError
    result = reboot_helper.load_platform_chassis()
    assert not result


def test_load_and_verify_chassis_fail():
    mock_load_platform_chassis.return_value = False
    assert not reboot_helper.load_and_verify("DPU1")


def test_load_and_verify_not_smartswitch(mock_is_smartswitch, mock_load_platform_chassis):
    mock_is_smartswitch.return_value = False
    mock_load_platform_chassis.return_value = True
    assert not reboot_helper.load_and_verify("DPU1")


def test_load_and_verify_not_found(mock_is_smartswitch, mock_load_platform_chassis, mock_get_dpu_list):
    mock_is_smartswitch.return_value = True
    mock_load_platform_chassis.return_value = True
    mock_get_dpu_list.return_value = ["dpu1"]

    assert not reboot_helper.load_and_verify("DPU2")


def test_load_and_verify_empty_dpu_list(mock_is_smartswitch, mock_load_platform_chassis, mock_get_dpu_list):
    mock_is_smartswitch.return_value = True
    mock_load_platform_chassis.return_value = True
    mock_get_dpu_list.return_value = []

    assert not reboot_helper.load_and_verify("DPU1")


def test_load_and_verify_success(mock_is_smartswitch, mock_load_platform_chassis, mock_get_dpu_list):
    mock_is_smartswitch.return_value = True
    mock_load_platform_chassis.return_value = True
    mock_get_dpu_list.return_value = ["dpu1"]

    result = reboot_helper.load_and_verify("DPU1")
    assert result


def test_reboot_dpu_load_and_verify_fail(mock_load_and_verify):
    mock_load_and_verify.return_value = False
    result = reboot_helper.reboot_dpu("DPU1", "DPU")
    assert not result


def test_reboot_dpu_not_implemented(mock_load_and_verify, mock_platform_chassis):
    mock_load_and_verify.return_value = True
    mock_platform_chassis.reboot.side_effect = NotImplementedError
    assert not reboot_helper.reboot_dpu("DPU1", 'DPU')


def test_reboot_dpu_success(mock_load_and_verify, mock_platform_chassis):
    mock_load_and_verify.return_value = True
    mock_platform_chassis.reboot.return_value = True
    assert reboot_helper.reboot_dpu("DPU1", "DPU")


def test_pci_detach_module_load_and_verify_fail(mock_load_and_verify):
    mock_load_and_verify.return_value = False
    assert not reboot_helper.pci_detach_module("DPU1")


def test_pci_detach_module_not_implemented(mock_load_and_verify, mock_platform_chassis):
    mock_load_and_verify.return_value = True
    mock_platform_chassis.pci_detach.side_effect = NotImplementedError

    assert not reboot_helper.pci_detach_module("DPU1")


def test_pci_detach_module_success(mock_load_and_verify, mock_platform_chassis):
    mock_load_and_verify.return_value = True
    mock_platform_chassis.pci_detach.return_value = True
    assert reboot_helper.pci_detach_module("DPU1")


def test_pci_reattach_module_load_and_verify_fail(mock_load_and_verify):
    mock_load_and_verify.return_value = False
    assert not reboot_helper.pci_reattach_module("DPU1")


def test_pci_reattach_module_not_implemented(mock_load_and_verify, mock_platform_chassis):
    mock_load_and_verify.return_value = True
    mock_platform_chassis.pci_reattach.side_effect = NotImplementedError
    assert not reboot_helper.pci_reattach_module("DPU1")


def test_pci_reattach_module_success(mock_load_and_verify, mock_platform_chassis):
    mock_load_and_verify.return_value = True
    mock_platform_chassis.pci_reattach.return_value = True
    assert reboot_helper.pci_reattach_module("DPU1")


def test_main_reboot_command_fail(monkeypatch):
    # Simulate command-line arguments for reboot
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'reboot', 'DPU1', 'DPU'])

    # Mock dependencies
    with patch('reboot_helper.reboot_dpu', return_value=False), \
         patch('sys.exit') as mock_exit:

        reboot_helper.main()

        # Check that sys.exit was called with EXIT_FAIL
        mock_exit.assert_called_once_with(reboot_helper.EXIT_FAIL)


def test_main_reboot_command_type_fail(monkeypatch):
    # Simulate command-line arguments for reboot
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'reboot', 'DPU1', 'UNKNOWN'])

    # Mock dependencies
    with patch('reboot_helper.reboot_dpu', return_value=False), \
         patch('sys.exit') as mock_exit:

        reboot_helper.main()

        # Check that sys.exit was called with EXIT_FAIL
        mock_exit.assert_called_once_with(reboot_helper.EXIT_FAIL)


def test_main_reboot_command_success(monkeypatch):
    # Simulate command-line arguments for reboot
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'reboot', 'DPU1', 'DPU'])

    # Mock dependencies
    with patch('reboot_helper.reboot_dpu', return_value=True) as mock_reboot_dpu, \
         patch('sys.exit') as mock_exit:

        reboot_helper.main()

        # Check that reboot_module was called
        mock_reboot_dpu.assert_called_once_with('DPU1', 'DPU')
        mock_exit.assert_not_called()


def test_main_pci_detach_command_fail(monkeypatch):
    # Simulate command-line arguments for reboot
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'pci_detach', 'DPU1'])

    # Mock dependencies
    with patch('reboot_helper.pci_detach_module', return_value=False), \
         patch('sys.exit') as mock_exit:

        reboot_helper.main()

        # Check that sys.exit was called with EXIT_FAIL
        mock_exit.assert_called_once_with(reboot_helper.EXIT_FAIL)


def test_main_pci_detach_command_success(monkeypatch):
    # Simulate command-line arguments for reboot
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'pci_detach', 'DPU1'])

    # Mock dependencies
    with patch('reboot_helper.pci_detach_module', return_value=True) as mock_reboot_module, \
         patch('sys.exit') as mock_exit:

        reboot_helper.main()

        # Check that pci_detach_module was called
        mock_reboot_module.assert_called_once_with('DPU1')
        mock_exit.assert_not_called()


def test_main_pci_reattach_command_fail(monkeypatch):
    # Simulate command-line arguments for reboot
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'pci_reattach', 'DPU1'])

    # Mock dependencies
    with patch('reboot_helper.pci_reattach_module', return_value=False), \
         patch('sys.exit') as mock_exit:

        reboot_helper.main()

        # Check that sys.exit was called with EXIT_FAIL
        mock_exit.assert_called_once_with(reboot_helper.EXIT_FAIL)


def test_main_pci_reattach_command_success(monkeypatch):
    # Simulate command-line arguments for reboot
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'pci_reattach', 'DPU1'])

    # Mock dependencies
    with patch('reboot_helper.pci_reattach_module', return_value=True) as mock_reboot_module, \
         patch('sys.exit') as mock_exit:

        reboot_helper.main()

        # Check that pci_reattach_module was called
        mock_reboot_module.assert_called_once_with('DPU1')
        mock_exit.assert_not_called()


def test_main_unknown_command(monkeypatch):
    # Simulate an unknown command
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'unknown', 'DPU1'])

    # Mock sys.exit and capture print output
    with patch('sys.exit') as mock_exit, patch('builtins.print') as mock_print:
        reboot_helper.main()

        # Check that the unknown command message was printed
        mock_print.assert_called_with("Unknown command: unknown")
        mock_exit.assert_called_once_with(reboot_helper.EXIT_FAIL)


def test_main_no_arguments(monkeypatch):
    # Simulate no command-line arguments
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py'])

    # Mock sys.exit and capture print output
    with patch('sys.exit') as mock_exit, patch('builtins.print') as mock_print:
        reboot_helper.main()

        # Check that the usage message was printed
        mock_print.assert_called_with("Usage: reboot_helper.py <command> <module_name> [reboot_type]")
        mock_exit.assert_called_once_with(reboot_helper.EXIT_FAIL)


def test_main_reboot_missing_reboot_type(monkeypatch):
    # Simulate command-line arguments for reboot without reboot_type
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'reboot', 'DPU1'])

    # Mock sys.exit and capture print output
    with patch('sys.exit') as mock_exit, patch('builtins.print') as mock_print:
        reboot_helper.main()

        # Check that the usage message was printed
        mock_print.assert_called_with("Usage: reboot_helper.py reboot <module_name> <reboot_type>")
        mock_exit.assert_called_once_with(reboot_helper.EXIT_FAIL)


def test_main_reboot_invalid_reboot_type(monkeypatch):
    # Simulate command-line arguments for reboot with invalid reboot_type
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'reboot', 'DPU1', 'INVALID'])

    # Mock dependencies
    with patch('reboot_helper.reboot_dpu', return_value=False), \
     patch('sys.exit') as mock_exit:
        reboot_helper.main()

        # Check that sys.exit was called with EXIT_FAIL
        mock_exit.assert_called_once_with(reboot_helper.EXIT_FAIL)


def test_main_pci_detach_invalid_module(monkeypatch):
    # Simulate command-line arguments for pci_detach with invalid module
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'pci_detach', 'INVALID'])

    # Mock dependencies
    with patch('reboot_helper.pci_detach_module', return_value=False), \
     patch('sys.exit') as mock_exit:

        reboot_helper.main()

        # Check that sys.exit was called with EXIT_FAIL
        mock_exit.assert_called_once_with(reboot_helper.EXIT_FAIL)


def test_main_pci_reattach_invalid_module(monkeypatch):
    # Simulate command-line arguments for pci_reattach with invalid module
    monkeypatch.setattr(sys, 'argv', ['reboot_helper.py', 'pci_reattach', 'INVALID'])

    # Mock dependencies
    with patch('reboot_helper.pci_reattach_module', return_value=False), \
     patch('sys.exit') as mock_exit:

        reboot_helper.main()

        # Check that sys.exit was called with EXIT_FAIL
        mock_exit.assert_called_once_with(reboot_helper.EXIT_FAIL)
