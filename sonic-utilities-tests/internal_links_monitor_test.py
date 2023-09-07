import imp
import os
import importlib
import mock_tables.dbconnector
import mock_tables.mock_multi_asic

int_errors = importlib.import_module("scripts.internal_links_monitor")

class TestPacketChassisInternalLinkMontoring(object):
    @classmethod
    def setup_class(cls):
        imp.reload(mock_tables.mock_multi_asic)
        mock_tables.dbconnector.load_namespace_config()        
        os.environ['UTILITIES_UNIT_TESTING'] = "2"

    @classmethod
    def teardown_class(cls):        
        os.environ['UTILITIES_UNIT_TESTING'] = "0"

    def test_get_port_status(self):
        port_name = 'Ethernet-BP16'
        namespace = 'asic0'
        link_monitor = int_errors.PacketChassisInternalLinkMontoring()
        assert link_monitor.get_port_status(namespace, port_name) == 'up'

    def test_isolate_lag_member(self):        
        port_name = 'Ethernet-BP4'
        namespace = 'asic0'
        link_monitor = int_errors.PacketChassisInternalLinkMontoring()
        assert link_monitor.get_port_status(namespace, port_name) == 'up'
        link_monitor.isolate_lag_member(namespace, port_name)
        assert link_monitor.get_port_status(namespace, port_name) == 'down'

    def test_get_lag_name_for_port(self):        
        port_name = 'Ethernet-BP4'
        namespace = 'asic0'
        link_monitor = int_errors.PacketChassisInternalLinkMontoring()
        assert link_monitor.get_lag_name_for_port(namespace, port_name) == 'PortChannel4001'

    def test_get_active_lag_member_count(self):        
        lag_name = 'PortChannel4001'
        namespace = 'asic0'
        link_monitor = int_errors.PacketChassisInternalLinkMontoring()
        assert link_monitor.get_active_lag_member_count(namespace, lag_name) == 4

    def test_mem_down_get_active_lag_member_count(self):        
        lag_name = 'PortChannel4001'
        namespace = 'asic0'
        port_name = 'Ethernet-BP4'
        link_monitor = int_errors.PacketChassisInternalLinkMontoring()
        link_monitor.isolate_lag_member(namespace, port_name)        
        assert link_monitor.get_active_lag_member_count(namespace, lag_name) == 3

    def test_get_min_links_for_lag(self):        
        lag_name = 'PortChannel4001'
        namespace = 'asic0'
        link_monitor = int_errors.PacketChassisInternalLinkMontoring()
        assert link_monitor.get_min_links_for_lag(namespace, lag_name) == 3

    def test_attempt_to_mitigate_ports(self):        
        port_list = ['Ethernet-BP0', 'Ethernet-BP4']
        namespace = 'asic0'
        lag_name = 'PortChannel4001'
        link_monitor = int_errors.PacketChassisInternalLinkMontoring()
        link_monitor.attempt_to_mitigate_ports(namespace, port_list)

        # Only one port should be brought down due to min_links check
        assert link_monitor.get_active_lag_member_count(namespace, lag_name) == 3

    def test_monitor(self):
        link_monitor = int_errors.PacketChassisInternalLinkMontoring()
        link_monitor.monitor()

        # Validation on asic0
        assert link_monitor.get_port_status('asic0', 'Ethernet-BP0') == 'up'
        assert link_monitor.get_port_status('asic0', 'Ethernet-BP4') == 'up'
        assert link_monitor.get_port_status('asic0', 'Ethernet-BP8') == 'down'
        # Action should be skipped due to min_links check
        assert link_monitor.get_port_status('asic0', 'Ethernet-BP16') == 'up'

        # Validation on asic1
        assert link_monitor.get_port_status('asic1', 'Ethernet-BP256') == 'down'
        assert link_monitor.get_port_status('asic1', 'Ethernet-BP260') == 'up'
        # Action should be skipped due to min_links check
        assert link_monitor.get_port_status('asic1', 'Ethernet-BP264') == 'up'