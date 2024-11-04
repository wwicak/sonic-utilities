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
ERROR_NOT_IMPLEMENTED = 1
ERROR_EXCEPTION = 2

# Global logger instance
log = logger.Logger(SYSLOG_IDENTIFIER)

# Global variable for platform chassis
platform_chassis = None


def get_all_dpus():
    """
    Retrieve a list of all DPUs (Data Processing Units) in the system.
    This function checks if the platform is a smartswitch and then loads the platform.json
    file to extract the DPUs dictionary. It converts the DPU names to uppercase and returns
    them as a list.

    Returns:
        list: A list of DPU names in uppercase.
    """
    dpu_list = []

    if not is_smartswitch():
        return dpu_list

    # Load platform.json
    platform_info = device_info.get_platform_info()
    platform = platform_info.get('platform')
    if not platform:
        log.log_error("Platform does not exist in platform_info")
        return dpu_list
    platform_json_path = os.path.join("/usr/share/sonic/device", platform, "platform.json")
    try:
        with open(platform_json_path, 'r') as platform_json:
            config_data = json.load(platform_json)

            # Extract DPUs dictionary
            dpus = config_data.get("DPUS", {})

            # Convert DPU names to uppercase and append to the list
            dpu_list = [dpu.upper() for dpu in dpus]
    except FileNotFoundError:
        log.log_error("platform.json not found")
        return dpu_list
    except json.JSONDecodeError:
        log.log_error("Failed to parse platform.json")
        return dpu_list
    except Exception as e:
        log.log_error("Unexpected error occurred while getting DPUs: {}".format(e))
        return dpu_list

    return dpu_list


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
    except Exception as e:
        raise RuntimeError("Failed to instantiate Chassis due to {}".format(str(e)))

    if platform_chassis is None:
        log.log_error("Platform chassis is not loaded")
        return False

    return True


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
    if hasattr(platform_chassis, 'reboot'):
        platform_chassis.reboot(module_name)
    else:
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
        sys.exit(ERROR_EXCEPTION)

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
    platform_json_path = os.path.join("/usr/share/sonic/device", platform, "platform.json")
    try:
        with open(platform_json_path, 'r') as platform_json:
            config_data = json.load(platform_json)

            # Check for any key matching the .DPU pattern
            for key in config_data.keys():
                if re.search(r'\.DPU$', key):
                    return True
    except FileNotFoundError:
        log.log_error("platform.json not found")
    except json.JSONDecodeError:
        log.log_error("Failed to parse platform.json")

    return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: reboot_helper.py <command> <module_name>")
        sys.exit(EXIT_FAIL)

    command = sys.argv[1]
    module_name = sys.argv[2]

    if command == "reboot":
        success = reboot_module(module_name)
        if is_dpu():
            print("Script is running on DPU module")
        else:
            sys.exit(EXIT_FAIL)
        if not is_dpu():
            sys.exit(ERROR_EXCEPTION)
    elif command == "is_dpu":
        if is_dpu():
            print("Script is running on DPU module")
        else:
            sys.exit(EXIT_FAIL)
    else:
        print("Unknown command: {command}")
        sys.exit(EXIT_FAIL)
