#!/usr/bin/env python3
# Copyright 2020 Canonical Ltd.
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

from typing import NoReturn
import unittest

import pod_spec


class TestPodSpec(unittest.TestCase):
    """Pod spec unit tests."""

    def test_make_pod_ports(self) -> NoReturn:
        """Testing make pod ports."""
        port = 9999

        expected_result = [
            {
                "name": "lcm",
                "containerPort": port,
                "protocol": "TCP",
            }
        ]

        pod_ports = pod_spec._make_pod_ports(9999)

        self.assertListEqual(expected_result, pod_ports)

    def test_make_pod_envconfig_without_vca_apiproxy(self) -> NoReturn:
        """Teting make pod envconfig without vca_apiproxy configuration."""
        config = {
            "database_commonkey": "commonkey",
            "log_level": "INFO",
            "vca_host": "vca",
            "vca_port": 1212,
            "vca_user": "vca_user",
            "vca_pubkey": "vca_pubkey",
            "vca_password": "vca_password",
            "vca_cacert": "vca_cacert",
            "vca_cloud": "vca_cloud",
            "vca_k8s_cloud": "vca_k8s_cloud",
        }
        relation_state = {
            "message_host": "kafka",
            "message_port": 2181,
            "database_uri": "mongodb://mongo",
            "ro_host": "ro",
            "ro_port": 9090,
        }

        expected_result = {
            "ALLOW_ANONYMOUS_LOGIN": "yes",
            "OSMLCM_GLOBAL_LOGLEVEL": config["log_level"],
            "OSMLCM_RO_HOST": relation_state["ro_host"],
            "OSMLCM_RO_PORT": relation_state["ro_port"],
            "OSMLCM_RO_TENANT": "osm",
            "OSMLCM_MESSAGE_DRIVER": "kafka",
            "OSMLCM_MESSAGE_HOST": relation_state["message_host"],
            "OSMLCM_MESSAGE_PORT": relation_state["message_port"],
            "OSMLCM_DATABASE_DRIVER": "mongo",
            "OSMLCM_DATABASE_URI": relation_state["database_uri"],
            "OSMLCM_DATABASE_COMMONKEY": config["database_commonkey"],
            "OSMLCM_STORAGE_DRIVER": "mongo",
            "OSMLCM_STORAGE_PATH": "/app/storage",
            "OSMLCM_STORAGE_COLLECTION": "files",
            "OSMLCM_STORAGE_URI": relation_state["database_uri"],
            "OSMLCM_VCA_HOST": config["vca_host"],
            "OSMLCM_VCA_PORT": config["vca_port"],
            "OSMLCM_VCA_USER": config["vca_user"],
            "OSMLCM_VCA_PUBKEY": config["vca_pubkey"],
            "OSMLCM_VCA_SECRET": config["vca_password"],
            "OSMLCM_VCA_CACERT": config["vca_cacert"],
            "OSMLCM_VCA_CLOUD": config["vca_cloud"],
            "OSMLCM_VCA_K8S_CLOUD": config["vca_k8s_cloud"],
        }

        pod_envconfig = pod_spec._make_pod_envconfig(config, relation_state)

        self.assertDictEqual(expected_result, pod_envconfig)

    def test_make_pod_envconfig_with_vca_apiproxy(self) -> NoReturn:
        """Teting make pod envconfig with vca_apiproxy configuration."""
        config = {
            "database_commonkey": "commonkey",
            "log_level": "INFO",
            "vca_host": "vca",
            "vca_port": 1212,
            "vca_user": "vca_user",
            "vca_pubkey": "vca_pubkey",
            "vca_password": "vca_password",
            "vca_cacert": "vca_cacert",
            "vca_cloud": "vca_cloud",
            "vca_k8s_cloud": "vca_k8s_cloud",
            "vca_apiproxy": "vca_apiproxy",
        }
        relation_state = {
            "message_host": "kafka",
            "message_port": 2181,
            "database_uri": "mongodb://mongo",
            "ro_host": "ro",
            "ro_port": 9090,
        }

        expected_result = {
            "ALLOW_ANONYMOUS_LOGIN": "yes",
            "OSMLCM_GLOBAL_LOGLEVEL": config["log_level"],
            "OSMLCM_RO_HOST": relation_state["ro_host"],
            "OSMLCM_RO_PORT": relation_state["ro_port"],
            "OSMLCM_RO_TENANT": "osm",
            "OSMLCM_MESSAGE_DRIVER": "kafka",
            "OSMLCM_MESSAGE_HOST": relation_state["message_host"],
            "OSMLCM_MESSAGE_PORT": relation_state["message_port"],
            "OSMLCM_DATABASE_DRIVER": "mongo",
            "OSMLCM_DATABASE_URI": relation_state["database_uri"],
            "OSMLCM_DATABASE_COMMONKEY": config["database_commonkey"],
            "OSMLCM_STORAGE_DRIVER": "mongo",
            "OSMLCM_STORAGE_PATH": "/app/storage",
            "OSMLCM_STORAGE_COLLECTION": "files",
            "OSMLCM_STORAGE_URI": relation_state["database_uri"],
            "OSMLCM_VCA_HOST": config["vca_host"],
            "OSMLCM_VCA_PORT": config["vca_port"],
            "OSMLCM_VCA_USER": config["vca_user"],
            "OSMLCM_VCA_PUBKEY": config["vca_pubkey"],
            "OSMLCM_VCA_SECRET": config["vca_password"],
            "OSMLCM_VCA_CACERT": config["vca_cacert"],
            "OSMLCM_VCA_CLOUD": config["vca_cloud"],
            "OSMLCM_VCA_K8S_CLOUD": config["vca_k8s_cloud"],
            "OSMLCM_VCA_APIPROXY": config["vca_apiproxy"],
        }

        pod_envconfig = pod_spec._make_pod_envconfig(config, relation_state)

        self.assertDictEqual(expected_result, pod_envconfig)

    def test_make_startup_probe(self) -> NoReturn:
        """Testing make startup probe."""
        expected_result = {
            "exec": {"command": ["/usr/bin/pgrep python3"]},
            "initialDelaySeconds": 60,
            "timeoutSeconds": 5,
        }

        startup_probe = pod_spec._make_startup_probe()

        self.assertDictEqual(expected_result, startup_probe)

    def test_make_readiness_probe(self) -> NoReturn:
        """Testing make readiness probe."""
        port = 9999

        expected_result = {
            "httpGet": {
                "path": "/osm/",
                "port": port,
            },
            "initialDelaySeconds": 45,
            "timeoutSeconds": 5,
        }

        readiness_probe = pod_spec._make_readiness_probe(port)

        self.assertDictEqual(expected_result, readiness_probe)

    def test_make_liveness_probe(self) -> NoReturn:
        """Testing make liveness probe."""
        port = 9999

        expected_result = {
            "httpGet": {
                "path": "/osm/",
                "port": port,
            },
            "initialDelaySeconds": 45,
            "timeoutSeconds": 5,
        }

        liveness_probe = pod_spec._make_liveness_probe(port)

        self.assertDictEqual(expected_result, liveness_probe)

    def test_make_pod_spec(self) -> NoReturn:
        """Testing make pod spec."""
        image_info = {"upstream-source": "opensourcemano/lcm:8"}
        config = {
            "database_commonkey": "commonkey",
            "log_level": "INFO",
            "vca_host": "vca",
            "vca_port": 1212,
            "vca_user": "vca_user",
            "vca_pubkey": "vca_pubkey",
            "vca_password": "vca_password",
            "vca_cacert": "vca_cacert",
            "vca_cloud": "vca_cloud",
            "vca_k8s_cloud": "vca_k8s_cloud",
            "vca_apiproxy": "vca_apiproxy",
        }
        relation_state = {
            "message_host": "kafka",
            "message_port": 2181,
            "database_uri": "mongodb://mongo",
            "ro_host": "ro",
            "ro_port": 9090,
        }
        app_name = "lcm"
        port = 9999

        expected_result = {
            "version": 3,
            "containers": [
                {
                    "name": app_name,
                    "imageDetails": image_info,
                    "imagePullPolicy": "Always",
                    "ports": [
                        {
                            "name": app_name,
                            "containerPort": port,
                            "protocol": "TCP",
                        }
                    ],
                    "envConfig": {
                        "ALLOW_ANONYMOUS_LOGIN": "yes",
                        "OSMLCM_GLOBAL_LOGLEVEL": config["log_level"],
                        "OSMLCM_RO_HOST": relation_state["ro_host"],
                        "OSMLCM_RO_PORT": relation_state["ro_port"],
                        "OSMLCM_RO_TENANT": "osm",
                        "OSMLCM_MESSAGE_DRIVER": "kafka",
                        "OSMLCM_MESSAGE_HOST": relation_state["message_host"],
                        "OSMLCM_MESSAGE_PORT": relation_state["message_port"],
                        "OSMLCM_DATABASE_DRIVER": "mongo",
                        "OSMLCM_DATABASE_URI": relation_state["database_uri"],
                        "OSMLCM_DATABASE_COMMONKEY": config["database_commonkey"],
                        "OSMLCM_STORAGE_DRIVER": "mongo",
                        "OSMLCM_STORAGE_PATH": "/app/storage",
                        "OSMLCM_STORAGE_COLLECTION": "files",
                        "OSMLCM_STORAGE_URI": relation_state["database_uri"],
                        "OSMLCM_VCA_HOST": config["vca_host"],
                        "OSMLCM_VCA_PORT": config["vca_port"],
                        "OSMLCM_VCA_USER": config["vca_user"],
                        "OSMLCM_VCA_PUBKEY": config["vca_pubkey"],
                        "OSMLCM_VCA_SECRET": config["vca_password"],
                        "OSMLCM_VCA_CACERT": config["vca_cacert"],
                        "OSMLCM_VCA_CLOUD": config["vca_cloud"],
                        "OSMLCM_VCA_K8S_CLOUD": config["vca_k8s_cloud"],
                        "OSMLCM_VCA_APIPROXY": config["vca_apiproxy"],
                    },
                }
            ],
            "kubernetesResources": {"ingressResources": []},
        }

        spec = pod_spec.make_pod_spec(
            image_info, config, relation_state, app_name, port
        )

        self.assertDictEqual(expected_result, spec)

    def test_make_pod_spec_with_vca_apiproxy(self) -> NoReturn:
        """Testing make pod spec with vca_apiproxy."""
        image_info = {"upstream-source": "opensourcemano/lcm:8"}
        config = {
            "database_commonkey": "commonkey",
            "log_level": "INFO",
            "vca_host": "vca",
            "vca_port": 1212,
            "vca_user": "vca_user",
            "vca_pubkey": "vca_pubkey",
            "vca_password": "vca_password",
            "vca_cacert": "vca_cacert",
            "vca_cloud": "vca_cloud",
            "vca_k8s_cloud": "vca_k8s_cloud",
        }
        relation_state = {
            "message_host": "kafka",
            "message_port": 2181,
            "database_uri": "mongodb://mongo",
            "ro_host": "ro",
            "ro_port": 9090,
        }
        app_name = "lcm"
        port = 9999

        expected_result = {
            "version": 3,
            "containers": [
                {
                    "name": app_name,
                    "imageDetails": image_info,
                    "imagePullPolicy": "Always",
                    "ports": [
                        {
                            "name": app_name,
                            "containerPort": port,
                            "protocol": "TCP",
                        }
                    ],
                    "envConfig": {
                        "ALLOW_ANONYMOUS_LOGIN": "yes",
                        "OSMLCM_GLOBAL_LOGLEVEL": config["log_level"],
                        "OSMLCM_RO_HOST": relation_state["ro_host"],
                        "OSMLCM_RO_PORT": relation_state["ro_port"],
                        "OSMLCM_RO_TENANT": "osm",
                        "OSMLCM_MESSAGE_DRIVER": "kafka",
                        "OSMLCM_MESSAGE_HOST": relation_state["message_host"],
                        "OSMLCM_MESSAGE_PORT": relation_state["message_port"],
                        "OSMLCM_DATABASE_DRIVER": "mongo",
                        "OSMLCM_DATABASE_URI": relation_state["database_uri"],
                        "OSMLCM_DATABASE_COMMONKEY": config["database_commonkey"],
                        "OSMLCM_STORAGE_DRIVER": "mongo",
                        "OSMLCM_STORAGE_PATH": "/app/storage",
                        "OSMLCM_STORAGE_COLLECTION": "files",
                        "OSMLCM_STORAGE_URI": relation_state["database_uri"],
                        "OSMLCM_VCA_HOST": config["vca_host"],
                        "OSMLCM_VCA_PORT": config["vca_port"],
                        "OSMLCM_VCA_USER": config["vca_user"],
                        "OSMLCM_VCA_PUBKEY": config["vca_pubkey"],
                        "OSMLCM_VCA_SECRET": config["vca_password"],
                        "OSMLCM_VCA_CACERT": config["vca_cacert"],
                        "OSMLCM_VCA_CLOUD": config["vca_cloud"],
                        "OSMLCM_VCA_K8S_CLOUD": config["vca_k8s_cloud"],
                    },
                }
            ],
            "kubernetesResources": {"ingressResources": []},
        }

        spec = pod_spec.make_pod_spec(
            image_info, config, relation_state, app_name, port
        )

        self.assertDictEqual(expected_result, spec)

    def test_make_pod_spec_without_image_info(self) -> NoReturn:
        """Testing make pod spec without image_info."""
        image_info = None
        config = {
            "database_commonkey": "commonkey",
            "log_level": "INFO",
            "vca_host": "vca",
            "vca_port": 1212,
            "vca_user": "vca_user",
            "vca_pubkey": "vca_pubkey",
            "vca_password": "vca_password",
            "vca_cacert": "vca_cacert",
            "vca_cloud": "vca_cloud",
            "vca_k8s_cloud": "vca_k8s_cloud",
            "vca_apiproxy": "vca_apiproxy",
        }
        relation_state = {
            "message_host": "kafka",
            "message_port": 2181,
            "database_uri": "mongodb://mongo",
            "ro_host": "ro",
            "ro_port": 9090,
        }
        app_name = "lcm"
        port = 9999

        spec = pod_spec.make_pod_spec(
            image_info, config, relation_state, app_name, port
        )

        self.assertIsNone(spec)

    def test_make_pod_spec_without_config(self) -> NoReturn:
        """Testing make pod spec without config."""
        image_info = {"upstream-source": "opensourcemano/lcm:8"}
        config = {}
        relation_state = {
            "message_host": "kafka",
            "message_port": 2181,
            "database_uri": "mongodb://mongo",
            "ro_host": "ro",
            "ro_port": 9090,
        }
        app_name = "lcm"
        port = 9999

        with self.assertRaises(ValueError):
            pod_spec.make_pod_spec(image_info, config, relation_state, app_name, port)

    def test_make_pod_spec_without_relation_state(self) -> NoReturn:
        """Testing make pod spec without relation_state."""
        image_info = {"upstream-source": "opensourcemano/lcm:8"}
        config = {
            "database_commonkey": "commonkey",
            "log_level": "INFO",
            "vca_host": "vca",
            "vca_port": 1212,
            "vca_user": "vca_user",
            "vca_pubkey": "vca_pubkey",
            "vca_password": "vca_password",
            "vca_cacert": "vca_cacert",
            "vca_cloud": "vca_cloud",
            "vca_k8s_cloud": "vca_k8s_cloud",
            "vca_apiproxy": "vca_apiproxy",
        }
        relation_state = {}
        app_name = "lcm"
        port = 9999

        with self.assertRaises(ValueError):
            pod_spec.make_pod_spec(image_info, config, relation_state, app_name, port)


if __name__ == "__main__":
    unittest.main()
