#!/usr/bin/env python3
#
# reboot_helper.py
#
# Utility helper for reboot within SONiC

import os
import re
import sys
import json
import sonic_platform
from sonic_py_common import logger, device_info
from utilities_common.chassis import is_smartswitch

SYSLOG_IDENTIFIER = "reboot_helper"

EXIT_FAIL = -1
EXIT_SUCCESS = 0

# Global logger instance
log = logger.Logger(SYSLOG_IDENTIFIER)

# Global variable for platform chassis
platform_chassis = None


def load_platform_chassis():
    """
    Load the platform chassis using the SONiC platform API.

    This function attempts to instantiate the platform chassis object.
    If successful, it sets the global variable `platform_chassis` to the instantiated object.

    Returns:
        bool: True if the platform chassis is successfully loaded, False otherwise.
    """
    global platform_chassis

    # Load new platform API class
    try:
        platform_chassis = sonic_platform.platform.Platform().get_chassis()
        if platform_chassis is None:
            log.log_error("Platform chassis is not loaded")
            return False
        return True
    except Exception as e:
        log.log_error(f"Failed to instantiate Chassis: {e}")
        return False


def load_platform_json(platform):
    """Load and return the content of platform.json."""
    platform_json_path = os.path.join("/usr/share/sonic/device", platform, "platform.json")
    try:
        with open(platform_json_path, 'r') as platform_json:
            return json.load(platform_json)
    except FileNotFoundError:
        log.log_error("platform.json not found")
    except json.JSONDecodeError:
        log.log_error("Failed to parse platform.json")
    return None


def get_all_dpus():
    """
    Retrieve a list of all DPUs (Data Processing Units) in the system.
    This function checks if the platform is a smartswitch and then loads the platform.json
    file to extract the DPUs dictionary. It converts the DPU names to uppercase and returns
    them as a list.

    Returns:
        list: A list of DPU names in uppercase.
    """
    if not is_smartswitch():
        return []

    platform_info = device_info.get_platform_info()
    platform = platform_info.get('platform')
    if not platform:
        log.log_error("Platform does not exist in platform_info")
        return []

    config_data = load_platform_json(platform)
    if config_data is None:
        return []

    dpus = config_data.get("DPUS", [])
    return [dpu.upper() for dpu in dpus]


def reboot_module(module_name):
    """
    Reboot the specified module by invoking the platform API.

    Args:
        module_name (str): The name of the module to reboot.

    Returns:
        bool: True if the reboot command was successfully sent, False otherwise.
    """
    # Load the platform chassis if not already loaded
    load_platform_chassis()

    if not is_smartswitch():
        log.log_error("Platform is not a smartswitch to reboot module")
        return False

    # Attempt to reboot the module
    if not hasattr(platform_chassis, 'reboot'):
        log.log_error("Reboot method not found in platform chassis")
        return False

    if module_name.upper() not in get_all_dpus():
        log.log_error("Module {} not found".format(module_name))
        return False

    log.log_info("Rebooting module {}...".format(module_name))
    try:
        platform_chassis.reboot(module_name)
        log.log_info("Reboot command sent for module {}".format(module_name))
    except NotImplementedError:
        raise NotImplementedError("Reboot not implemented on this platform: {type(e).__name__}")
    except Exception as e:
        log.log_error("Unexpected error occurred while rebooting module {}: {}".format(module_name, e))
        return False

    return True


def is_dpu():
    """Check if script is running on DPU module"""

    # Load the platform chassis if not already loaded
    load_platform_chassis()

    if not is_smartswitch():
        return False

    # Load platform.json
    platform_info = device_info.get_platform_info()
    platform = platform_info.get('platform')
    if not platform:
        log.log_error("Platform does not exist in platform_info")
        return False

    config_data = load_platform_json(platform)
    if config_data is None:
        return False

    return any(re.search(r'\.DPU$', key) for key in config_data.keys())


def pci_detach_module(module_name):
    """
    Detach the specified module by invoking the platform API.

    Args:
        module_name (str): The name of the module to detach.

    Returns:
        bool: True if the detach command was successfully sent, False otherwise.
    """

    # Load the platform chassis if not already loaded
    load_platform_chassis()

    if not is_smartswitch():
        log.log_error("Platform is not a smartswitch to detach module")
        return False

    # Attempt to detach the module
    if not hasattr(platform_chassis, 'pci_detach'):
        log.log_error("PCI detach method not found in platform chassis")
        return False

    if module_name.upper() not in get_all_dpus():
        log.log_error("Module {} not found".format(module_name))
        return False

    log.log_info("Detaching module {}...".format(module_name))
    try:
        platform_chassis.pci_detach(module_name)
        log.log_info("Detach command sent for module {}".format(module_name))
        return True
    except NotImplementedError:
        raise NotImplementedError("PCI detach not implemented on this platform: {type(e).__name__}")
    except Exception as e:
        log.log_error("Unexpected error occurred while detaching module {}: {}".format(module_name, e))
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: reboot_helper.py <command> [module_name]")
        sys.exit(EXIT_FAIL)

    command = sys.argv[1]

    if command == "reboot" or command == "pci_detach":
        if len(sys.argv) < 3:
            print("Usage: reboot_helper.py <command> <module_name>")
            sys.exit(EXIT_FAIL)
        module_name = sys.argv[2]

        if command == "reboot":
            success = reboot_module(module_name)
            if not success:
                sys.exit(EXIT_FAIL)
        elif command == "pci_detach":
            success = pci_detach_module(module_name)
            if not success:
                sys.exit(EXIT_FAIL)
    elif command == "is_dpu":
        if is_dpu():
            print("Script is running on DPU module")
        else:
            sys.exit(EXIT_FAIL)
    else:
        print(f"Unknown command: {command}")
        sys.exit(EXIT_FAIL)


if __name__ == "__main__":
    main()
