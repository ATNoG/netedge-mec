#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact: legal@canonical.com
#
# To get in touch with the maintainers, please contact:
# osm-charmers@lists.launchpad.net
##

import sys
from typing import NoReturn
import unittest

from charm import LcmCharm
import mock
from ops.model import ActiveStatus, BlockedStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    """LCM Charm unit tests."""

    def setUp(self) -> NoReturn:
        """Test setup"""
        self.image_info = sys.modules["oci_image"].OCIImageResource().fetch()
        self.harness = Harness(LcmCharm)
        self.harness.set_leader(is_leader=True)
        self.harness.begin()
        self.config = {
            "vca_host": "192.168.0.13",
            "vca_port": 17070,
            "vca_user": "admin",
            "vca_secret": "admin",
            "vca_pubkey": "key",
            "vca_cacert": "cacert",
            "vca_cloud": "cloud",
            "vca_k8s_cloud": "k8scloud",
            "database_commonkey": "commonkey",
            "mongodb_uri": "",
            "log_level": "INFO",
        }
        self.harness.update_config(self.config)

    def test_config_changed_no_relations(
        self,
    ) -> NoReturn:
        """Test ingress resources without HTTP."""

        self.harness.charm.on.config_changed.emit()

        # Assertions
        self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)
        self.assertTrue(
            all(
                relation in self.harness.charm.unit.status.message
                for relation in ["mongodb", "kafka", "ro"]
            )
        )

    def test_config_changed_non_leader(
        self,
    ) -> NoReturn:
        """Test ingress resources without HTTP."""
        self.harness.set_leader(is_leader=False)
        self.harness.charm.on.config_changed.emit()

        # Assertions
        self.assertIsInstance(self.harness.charm.unit.status, ActiveStatus)

    def test_with_relations_and_mongodb_config(
        self,
    ) -> NoReturn:
        "Test with relations and mongodb config"
        self.initialize_kafka_relation()
        self.initialize_mongo_config()
        self.initialize_ro_relation()
        # Verifying status
        self.assertNotIsInstance(self.harness.charm.unit.status, BlockedStatus)

    def test_with_relations(
        self,
    ) -> NoReturn:
        "Test with relations (internal)"
        self.initialize_kafka_relation()
        self.initialize_mongo_relation()
        self.initialize_ro_relation()
        # Verifying status
        self.assertNotIsInstance(self.harness.charm.unit.status, BlockedStatus)

    def test_exception_mongodb_relation_and_config(
        self,
    ) -> NoReturn:
        "Test with all relations and config for mongodb. Must fail"
        self.initialize_mongo_relation()
        self.initialize_mongo_config()
        # Verifying status
        self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)

    # def test_build_pod_spec(
    #     self,
    # ) -> NoReturn:
    #     expected_config = {
    #         "OSMLCM_GLOBAL_LOGLEVEL": self.config["log_level"],
    #         "OSMLCM_DATABASE_COMMONKEY": self.config["database_commonkey"],
    #     }
    #     expected_config.update(
    #         {
    #             f"OSMLCM_{k.upper()}": v
    #             for k, v in self.config.items()
    #             if k.startswith("vca_")
    #         }
    #     )
    #     self.harness.charm._check_missing_dependencies = mock.Mock()
    #     pod_spec = self.harness.charm.build_pod_spec(
    #         {"imageDetails": {"imagePath": "lcm-image"}}
    #     )
    #     actual_config = pod_spec["containers"][0]["envConfig"]

    #     self.assertDictContainsSubset(
    #         expected_config,
    #         actual_config,
    #     )
    #     for config_key in actual_config:
    #         self.assertNotIn("VCA_MODEL_CONFIG", config_key)

    def test_build_pod_spec_with_model_config(
        self,
    ) -> NoReturn:
        self.harness.update_config(
            {
                "vca_model_config_agent_metadata_url": "string",
                "vca_model_config_agent_stream": "string",
                "vca_model_config_apt_ftp_proxy": "string",
                "vca_model_config_apt_http_proxy": "string",
                "vca_model_config_apt_https_proxy": "string",
                "vca_model_config_apt_mirror": "string",
                "vca_model_config_apt_no_proxy": "string",
                "vca_model_config_automatically_retry_hooks": False,
                "vca_model_config_backup_dir": "string",
                "vca_model_config_cloudinit_userdata": "string",
                "vca_model_config_container_image_metadata_url": "string",
                "vca_model_config_container_image_stream": "string",
                "vca_model_config_container_inherit_properties": "string",
                "vca_model_config_container_networking_method": "string",
                "vca_model_config_default_series": "string",
                "vca_model_config_default_space": "string",
                "vca_model_config_development": False,
                "vca_model_config_disable_network_management": False,
                "vca_model_config_egress_subnets": "string",
                "vca_model_config_enable_os_refresh_update": False,
                "vca_model_config_enable_os_upgrade": False,
                "vca_model_config_fan_config": "string",
                "vca_model_config_firewall_mode": "string",
                "vca_model_config_ftp_proxy": "string",
                "vca_model_config_http_proxy": "string",
                "vca_model_config_https_proxy": "string",
                "vca_model_config_ignore_machine_addresses": False,
                "vca_model_config_image_metadata_url": "string",
                "vca_model_config_image_stream": "string",
                "vca_model_config_juju_ftp_proxy": "string",
                "vca_model_config_juju_http_proxy": "string",
                "vca_model_config_juju_https_proxy": "string",
                "vca_model_config_juju_no_proxy": "string",
                "vca_model_config_logforward_enabled": False,
                "vca_model_config_logging_config": "string",
                "vca_model_config_lxd_snap_channel": "string",
                "vca_model_config_max_action_results_age": "string",
                "vca_model_config_max_action_results_size": "string",
                "vca_model_config_max_status_history_age": "string",
                "vca_model_config_max_status_history_size": "string",
                "vca_model_config_net_bond_reconfigure_delay": "string",
                "vca_model_config_no_proxy": "string",
                "vca_model_config_provisioner_harvest_mode": "string",
                "vca_model_config_proxy_ssh": False,
                "vca_model_config_snap_http_proxy": "string",
                "vca_model_config_snap_https_proxy": "string",
                "vca_model_config_snap_store_assertions": "string",
                "vca_model_config_snap_store_proxy": "string",
                "vca_model_config_snap_store_proxy_url": "string",
                "vca_model_config_ssl_hostname_verification": False,
                "vca_model_config_test_mode": False,
                "vca_model_config_transmit_vendor_metrics": False,
                "vca_model_config_update_status_hook_interval": "string",
            }
        )
        expected_config = {
            f"OSMLCM_{k.upper()}": v
            for k, v in self.config.items()
            if k.startswith("vca_model_config_")
        }

        self.harness.charm._check_missing_dependencies = mock.Mock()
        pod_spec = self.harness.charm.build_pod_spec(
            {"imageDetails": {"imagePath": "lcm-image"}}
        )
        actual_config = pod_spec["containers"][0]["envConfig"]

        self.assertDictContainsSubset(
            expected_config,
            actual_config,
        )

    def initialize_kafka_relation(self):
        kafka_relation_id = self.harness.add_relation("kafka", "kafka")
        self.harness.add_relation_unit(kafka_relation_id, "kafka/0")
        self.harness.update_relation_data(
            kafka_relation_id, "kafka", {"host": "kafka", "port": 9092}
        )

    def initialize_mongo_config(self):
        self.harness.update_config({"mongodb_uri": "mongodb://mongo:27017"})

    def initialize_mongo_relation(self):
        mongodb_relation_id = self.harness.add_relation("mongodb", "mongodb")
        self.harness.add_relation_unit(mongodb_relation_id, "mongodb/0")
        self.harness.update_relation_data(
            mongodb_relation_id,
            "mongodb/0",
            {"connection_string": "mongodb://mongo:27017"},
        )

    def initialize_ro_relation(self):
        http_relation_id = self.harness.add_relation("ro", "ro")
        self.harness.add_relation_unit(http_relation_id, "ro")
        self.harness.update_relation_data(
            http_relation_id,
            "ro",
            {"host": "ro", "port": 9090},
        )


if __name__ == "__main__":
    unittest.main()


# class TestCharm(unittest.TestCase):
#     """LCM Charm unit tests."""

#     def setUp(self) -> NoReturn:
#         """Test setup"""
#         self.harness = Harness(LcmCharm)
#         self.harness.set_leader(is_leader=True)
#         self.harness.begin()

#     def test_on_start_without_relations(self) -> NoReturn:
#         """Test installation without any relation."""
#         self.harness.charm.on.start.emit()

#         # Verifying status
#         self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)

#         # Verifying status message
#         self.assertGreater(len(self.harness.charm.unit.status.message), 0)
#         self.assertTrue(
#             self.harness.charm.unit.status.message.startswith("Waiting for ")
#         )
#         self.assertIn("kafka", self.harness.charm.unit.status.message)
#         self.assertIn("mongodb", self.harness.charm.unit.status.message)
#         self.assertIn("ro", self.harness.charm.unit.status.message)
#         self.assertTrue(self.harness.charm.unit.status.message.endswith(" relations"))

#     def test_on_start_with_relations(self) -> NoReturn:
#         """Test deployment without keystone."""
#         expected_result = {
#             "version": 3,
#             "containers": [
#                 {
#                     "name": "lcm",
#                     "imageDetails": self.harness.charm.image.fetch(),
#                     "imagePullPolicy": "Always",
#                     "ports": [
#                         {
#                             "name": "lcm",
#                             "containerPort": 9999,
#                             "protocol": "TCP",
#                         }
#                     ],
#                     "envConfig": {
#                         "ALLOW_ANONYMOUS_LOGIN": "yes",
#                         "OSMLCM_GLOBAL_LOGLEVEL": "INFO",
#                         "OSMLCM_RO_HOST": "ro",
#                         "OSMLCM_RO_PORT": 9090,
#                         "OSMLCM_RO_TENANT": "osm",
#                         "OSMLCM_MESSAGE_DRIVER": "kafka",
#                         "OSMLCM_MESSAGE_HOST": "kafka",
#                         "OSMLCM_MESSAGE_PORT": 9092,
#                         "OSMLCM_DATABASE_DRIVER": "mongo",
#                         "OSMLCM_DATABASE_URI": "mongodb://mongo:27017",
#                         "OSMLCM_DATABASE_COMMONKEY": "osm",
#                         "OSMLCM_STORAGE_DRIVER": "mongo",
#                         "OSMLCM_STORAGE_PATH": "/app/storage",
#                         "OSMLCM_STORAGE_COLLECTION": "files",
#                         "OSMLCM_STORAGE_URI": "mongodb://mongo:27017",
#                         "OSMLCM_VCA_HOST": "admin",
#                         "OSMLCM_VCA_PORT": 17070,
#                         "OSMLCM_VCA_USER": "admin",
#                         "OSMLCM_VCA_PUBKEY": "secret",
#                         "OSMLCM_VCA_SECRET": "secret",
#                         "OSMLCM_VCA_CACERT": "",
#                         "OSMLCM_VCA_CLOUD": "localhost",
#                         "OSMLCM_VCA_K8S_CLOUD": "k8scloud",
#                     },
#                 }
#             ],
#             "kubernetesResources": {"ingressResources": []},
#         }

#         self.harness.charm.on.start.emit()

#         # Check if kafka datastore is initialized
#         self.assertIsNone(self.harness.charm.state.message_host)
#         self.assertIsNone(self.harness.charm.state.message_port)

#         # Check if mongodb datastore is initialized
#         self.assertIsNone(self.harness.charm.state.database_uri)

#         # Check if RO datastore is initialized
#         self.assertIsNone(self.harness.charm.state.ro_host)
#         self.assertIsNone(self.harness.charm.state.ro_port)

#         # Initializing the kafka relation
#         kafka_relation_id = self.harness.add_relation("kafka", "kafka")
#         self.harness.add_relation_unit(kafka_relation_id, "kafka/0")
#         self.harness.update_relation_data(
#             kafka_relation_id, "kafka/0", {"host": "kafka", "port": 9092}
#         )

#         # Initializing the mongo relation
#         mongodb_relation_id = self.harness.add_relation("mongodb", "mongodb")
#         self.harness.add_relation_unit(mongodb_relation_id, "mongodb/0")
#         self.harness.update_relation_data(
#             mongodb_relation_id,
#             "mongodb/0",
#             {"connection_string": "mongodb://mongo:27017"},
#         )

#         # Initializing the RO relation
#         ro_relation_id = self.harness.add_relation("ro", "ro")
#         self.harness.add_relation_unit(ro_relation_id, "ro/0")
#         self.harness.update_relation_data(
#             ro_relation_id, "ro/0", {"host": "ro", "port": 9090}
#         )

#         # Checking if kafka data is stored
#         self.assertEqual(self.harness.charm.state.message_host, "kafka")
#         self.assertEqual(self.harness.charm.state.message_port, 9092)

#         # Checking if mongodb data is stored
#         self.assertEqual(self.harness.charm.state.database_uri, "mongodb://mongo:27017")

#         # Checking if RO data is stored
#         self.assertEqual(self.harness.charm.state.ro_host, "ro")
#         self.assertEqual(self.harness.charm.state.ro_port, 9090)

#         # Verifying status
#         self.assertNotIsInstance(self.harness.charm.unit.status, BlockedStatus)

#         pod_spec, _ = self.harness.get_pod_spec()

#         self.assertDictEqual(expected_result, pod_spec)

#     def test_on_kafka_relation_unit_changed(self) -> NoReturn:
#         """Test to see if kafka relation is updated."""
#         self.harness.charm.on.start.emit()

#         self.assertIsNone(self.harness.charm.state.message_host)
#         self.assertIsNone(self.harness.charm.state.message_port)

#         relation_id = self.harness.add_relation("kafka", "kafka")
#         self.harness.add_relation_unit(relation_id, "kafka/0")
#         self.harness.update_relation_data(
#             relation_id, "kafka/0", {"host": "kafka", "port": 9092}
#         )

#         self.assertEqual(self.harness.charm.state.message_host, "kafka")
#         self.assertEqual(self.harness.charm.state.message_port, 9092)

#         # Verifying status
#         self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)

#         # Verifying status message
#         self.assertGreater(len(self.harness.charm.unit.status.message), 0)
#         self.assertTrue(
#             self.harness.charm.unit.status.message.startswith("Waiting for ")
#         )
#         self.assertNotIn("kafka", self.harness.charm.unit.status.message)
#         self.assertIn("mongodb", self.harness.charm.unit.status.message)
#         self.assertIn("ro", self.harness.charm.unit.status.message)
#         self.assertTrue(self.harness.charm.unit.status.message.endswith(" relations"))

#     def test_on_mongodb_unit_relation_changed(self) -> NoReturn:
#         """Test to see if mongodb relation is updated."""
#         self.harness.charm.on.start.emit()

#         self.assertIsNone(self.harness.charm.state.database_uri)

#         relation_id = self.harness.add_relation("mongodb", "mongodb")
#         self.harness.add_relation_unit(relation_id, "mongodb/0")
#         self.harness.update_relation_data(
#             relation_id, "mongodb/0", {"connection_string": "mongodb://mongo:27017"}
#         )

#         self.assertEqual(self.harness.charm.state.database_uri, "mongodb://mongo:27017")

#         # Verifying status
#         self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)

#         # Verifying status message
#         self.assertGreater(len(self.harness.charm.unit.status.message), 0)
#         self.assertTrue(
#             self.harness.charm.unit.status.message.startswith("Waiting for ")
#         )
#         self.assertIn("kafka", self.harness.charm.unit.status.message)
#         self.assertNotIn("mongodb", self.harness.charm.unit.status.message)
#         self.assertIn("ro", self.harness.charm.unit.status.message)
#         self.assertTrue(self.harness.charm.unit.status.message.endswith(" relations"))

#     def test_on_ro_unit_relation_changed(self) -> NoReturn:
#         """Test to see if RO relation is updated."""
#         self.harness.charm.on.start.emit()

#         self.assertIsNone(self.harness.charm.state.ro_host)
#         self.assertIsNone(self.harness.charm.state.ro_port)

#         relation_id = self.harness.add_relation("ro", "ro")
#         self.harness.add_relation_unit(relation_id, "ro/0")
#         self.harness.update_relation_data(
#             relation_id, "ro/0", {"host": "ro", "port": 9090}
#         )

#         self.assertEqual(self.harness.charm.state.ro_host, "ro")
#         self.assertEqual(self.harness.charm.state.ro_port, 9090)

#         # Verifying status
#         self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)

#         # Verifying status message
#         self.assertGreater(len(self.harness.charm.unit.status.message), 0)
#         self.assertTrue(
#             self.harness.charm.unit.status.message.startswith("Waiting for ")
#         )
#         self.assertIn("kafka", self.harness.charm.unit.status.message)
#         self.assertIn("mongodb", self.harness.charm.unit.status.message)
#         self.assertNotIn("ro", self.harness.charm.unit.status.message)
#         self.assertTrue(self.harness.charm.unit.status.message.endswith(" relations"))


# if __name__ == "__main__":
#     unittest.main()
