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


from charm import NbiCharm
from ops.model import ActiveStatus, BlockedStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    """Prometheus Charm unit tests."""

    def setUp(self) -> NoReturn:
        """Test setup"""
        self.image_info = sys.modules["oci_image"].OCIImageResource().fetch()
        self.harness = Harness(NbiCharm)
        self.harness.set_leader(is_leader=True)
        self.harness.begin()
        self.config = {
            "enable_test": False,
            "auth_backend": "internal",
            "database_commonkey": "key",
            "mongodb_uri": "",
            "log_level": "INFO",
            "max_file_size": 0,
            "ingress_whitelist_source_range": "",
            "tls_secret_name": "",
            "site_url": "https://nbi.192.168.100.100.nip.io",
            "cluster_issuer": "vault-issuer",
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
                for relation in ["mongodb", "kafka", "prometheus"]
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

    def test_with_relations_internal_and_mongodb_config(
        self,
    ) -> NoReturn:
        "Test with relations and mongodb config (internal)"
        self.initialize_kafka_relation()
        self.initialize_mongo_config()
        self.initialize_prometheus_relation()
        # Verifying status
        self.assertNotIsInstance(self.harness.charm.unit.status, BlockedStatus)

    def test_with_relations_internal(
        self,
    ) -> NoReturn:
        "Test with relations (internal)"
        self.initialize_kafka_relation()
        self.initialize_mongo_relation()
        self.initialize_prometheus_relation()
        # Verifying status
        self.assertNotIsInstance(self.harness.charm.unit.status, BlockedStatus)

    def test_with_relations_and_mongodb_config_with_keystone_missing(
        self,
    ) -> NoReturn:
        "Test with relations and mongodb config (keystone)"
        self.harness.update_config({"auth_backend": "keystone"})
        self.initialize_kafka_relation()
        self.initialize_mongo_config()
        self.initialize_prometheus_relation()
        # Verifying status
        self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)
        self.assertTrue("keystone" in self.harness.charm.unit.status.message)

    def test_with_relations_keystone_missing(
        self,
    ) -> NoReturn:
        "Test with relations (keystone)"
        self.harness.update_config({"auth_backend": "keystone"})
        self.initialize_kafka_relation()
        self.initialize_mongo_relation()
        self.initialize_prometheus_relation()
        # Verifying status
        self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)
        self.assertTrue("keystone" in self.harness.charm.unit.status.message)

    def test_with_relations_and_mongodb_config_with_keystone(
        self,
    ) -> NoReturn:
        "Test with relations (keystone)"
        self.harness.update_config({"auth_backend": "keystone"})
        self.initialize_kafka_relation()
        self.initialize_mongo_config()
        self.initialize_prometheus_relation()
        self.initialize_keystone_relation()
        # Verifying status
        self.assertNotIsInstance(self.harness.charm.unit.status, BlockedStatus)

    def test_with_relations_keystone(
        self,
    ) -> NoReturn:
        "Test with relations (keystone)"
        self.harness.update_config({"auth_backend": "keystone"})
        self.initialize_kafka_relation()
        self.initialize_mongo_relation()
        self.initialize_prometheus_relation()
        self.initialize_keystone_relation()
        # Verifying status
        self.assertNotIsInstance(self.harness.charm.unit.status, BlockedStatus)

    def test_mongodb_exception_relation_and_config(
        self,
    ) -> NoReturn:
        self.initialize_mongo_config()
        self.initialize_mongo_relation()
        # Verifying status
        self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)

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

    def initialize_keystone_relation(self):
        keystone_relation_id = self.harness.add_relation("keystone", "keystone")
        self.harness.add_relation_unit(keystone_relation_id, "keystone/0")
        self.harness.update_relation_data(
            keystone_relation_id,
            "keystone",
            {
                "host": "host",
                "port": 5000,
                "user_domain_name": "ud",
                "project_domain_name": "pd",
                "username": "u",
                "password": "p",
                "service": "s",
                "keystone_db_password": "something",
                "region_id": "something",
                "admin_username": "something",
                "admin_password": "something",
                "admin_project_name": "something",
            },
        )

    def initialize_prometheus_relation(self):
        prometheus_relation_id = self.harness.add_relation("prometheus", "prometheus")
        self.harness.add_relation_unit(prometheus_relation_id, "prometheus/0")
        self.harness.update_relation_data(
            prometheus_relation_id,
            "prometheus",
            {"hostname": "prometheus", "port": 9090},
        )


if __name__ == "__main__":
    unittest.main()


# class TestCharm(unittest.TestCase):
#     """Prometheus Charm unit tests."""

#     def setUp(self) -> NoReturn:
#         """Test setup"""
#         self.image_info = sys.modules["oci_image"].OCIImageResource().fetch()
#         self.harness = Harness(NbiCharm)
#         self.harness.set_leader(is_leader=True)
#         self.harness.begin()
#         self.config = {
#             "enable_ng_ro": True,
#             "database_commonkey": "commonkey",
#             "log_level": "INFO",
#             "vim_database": "db_name",
#             "ro_database": "ro_db_name",
#             "openmano_tenant": "mano",
#         }

#     def test_config_changed_no_relations(
#         self,
#     ) -> NoReturn:
#         """Test ingress resources without HTTP."""

#         self.harness.charm.on.config_changed.emit()

#         # Assertions
#         self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)
#         self.assertTrue(
#             all(
#                 relation in self.harness.charm.unit.status.message
#                 for relation in ["mongodb", "kafka"]
#             )
#         )

#         # Disable ng-ro
#         self.harness.update_config({"enable_ng_ro": False})
#         self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)
#         self.assertTrue(
#             all(
#                 relation in self.harness.charm.unit.status.message
#                 for relation in ["mysql"]
#             )
#         )

#     def test_config_changed_non_leader(
#         self,
#     ) -> NoReturn:
#         """Test ingress resources without HTTP."""
#         self.harness.set_leader(is_leader=False)
#         self.harness.charm.on.config_changed.emit()

#         # Assertions
#         self.assertIsInstance(self.harness.charm.unit.status, ActiveStatus)

#     def test_with_relations_ng(
#         self,
#     ) -> NoReturn:
#         "Test with relations (ng-ro)"

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

#         self.harness.charm.on.config_changed.emit()

#         # Verifying status
#         self.assertNotIsInstance(self.harness.charm.unit.status, BlockedStatus)


# if __name__ == "__main__":
#     unittest.main()
