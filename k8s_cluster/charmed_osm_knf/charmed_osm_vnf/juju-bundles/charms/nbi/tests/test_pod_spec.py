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
                "name": "nbi",
                "containerPort": port,
                "protocol": "TCP",
            }
        ]

        pod_ports = pod_spec._make_pod_ports(port)

        self.assertListEqual(expected_result, pod_ports)

    def test_make_pod_envconfig_without_keystone(self) -> NoReturn:
        """Teting make pod envconfig without Keystone."""
        config = {
            "enable_test": False,
            "database_commonkey": "commonkey",
            "log_level": "DEBUG",
            "auth_backend": "internal",
        }
        relation_state = {
            "message_host": "kafka",
            "message_port": 9090,
            "database_uri": "mongodb://mongo",
            "prometheus_host": "prometheus",
            "prometheus_port": 9082,
        }

        expected_result = {
            "ALLOW_ANONYMOUS_LOGIN": "yes",
            "OSMNBI_SERVER_ENABLE_TEST": config["enable_test"],
            "OSMNBI_STATIC_DIR": "/app/osm_nbi/html_public",
            "OSMNBI_MESSAGE_HOST": relation_state["message_host"],
            "OSMNBI_MESSAGE_DRIVER": "kafka",
            "OSMNBI_MESSAGE_PORT": relation_state["message_port"],
            "OSMNBI_DATABASE_DRIVER": "mongo",
            "OSMNBI_DATABASE_URI": relation_state["database_uri"],
            "OSMNBI_DATABASE_COMMONKEY": config["database_commonkey"],
            "OSMNBI_STORAGE_DRIVER": "mongo",
            "OSMNBI_STORAGE_PATH": "/app/storage",
            "OSMNBI_STORAGE_COLLECTION": "files",
            "OSMNBI_STORAGE_URI": relation_state["database_uri"],
            "OSMNBI_PROMETHEUS_HOST": relation_state["prometheus_host"],
            "OSMNBI_PROMETHEUS_PORT": relation_state["prometheus_port"],
            "OSMNBI_LOG_LEVEL": config["log_level"],
            "OSMNBI_AUTHENTICATION_BACKEND": config["auth_backend"],
        }

        pod_envconfig = pod_spec._make_pod_envconfig(config, relation_state)

        self.assertDictEqual(expected_result, pod_envconfig)

    def test_make_pod_envconfig_with_keystone(self) -> NoReturn:
        """Teting make pod envconfig with Keystone."""
        config = {
            "enable_test": False,
            "database_commonkey": "commonkey",
            "log_level": "DEBUG",
            "auth_backend": "keystone",
        }
        relation_state = {
            "message_host": "kafka",
            "message_port": 9090,
            "database_uri": "mongodb://mongo",
            "prometheus_host": "prometheus",
            "prometheus_port": 9082,
            "keystone_host": "keystone",
            "keystone_port": 5000,
            "keystone_user_domain_name": "user_domain",
            "keystone_project_domain_name": "project_domain",
            "keystone_username": "username",
            "keystone_password": "password",
            "keystone_service": "service",
        }

        expected_result = {
            "ALLOW_ANONYMOUS_LOGIN": "yes",
            "OSMNBI_SERVER_ENABLE_TEST": config["enable_test"],
            "OSMNBI_STATIC_DIR": "/app/osm_nbi/html_public",
            "OSMNBI_MESSAGE_HOST": relation_state["message_host"],
            "OSMNBI_MESSAGE_DRIVER": "kafka",
            "OSMNBI_MESSAGE_PORT": relation_state["message_port"],
            "OSMNBI_DATABASE_DRIVER": "mongo",
            "OSMNBI_DATABASE_URI": relation_state["database_uri"],
            "OSMNBI_DATABASE_COMMONKEY": config["database_commonkey"],
            "OSMNBI_STORAGE_DRIVER": "mongo",
            "OSMNBI_STORAGE_PATH": "/app/storage",
            "OSMNBI_STORAGE_COLLECTION": "files",
            "OSMNBI_STORAGE_URI": relation_state["database_uri"],
            "OSMNBI_PROMETHEUS_HOST": relation_state["prometheus_host"],
            "OSMNBI_PROMETHEUS_PORT": relation_state["prometheus_port"],
            "OSMNBI_LOG_LEVEL": config["log_level"],
            "OSMNBI_AUTHENTICATION_BACKEND": config["auth_backend"],
            "OSMNBI_AUTHENTICATION_AUTH_URL": relation_state["keystone_host"],
            "OSMNBI_AUTHENTICATION_AUTH_PORT": relation_state["keystone_port"],
            "OSMNBI_AUTHENTICATION_USER_DOMAIN_NAME": relation_state[
                "keystone_user_domain_name"
            ],
            "OSMNBI_AUTHENTICATION_PROJECT_DOMAIN_NAME": relation_state[
                "keystone_project_domain_name"
            ],
            "OSMNBI_AUTHENTICATION_SERVICE_USERNAME": relation_state[
                "keystone_username"
            ],
            "OSMNBI_AUTHENTICATION_SERVICE_PASSWORD": relation_state[
                "keystone_password"
            ],
            "OSMNBI_AUTHENTICATION_SERVICE_PROJECT": relation_state["keystone_service"],
        }

        pod_envconfig = pod_spec._make_pod_envconfig(config, relation_state)

        self.assertDictEqual(expected_result, pod_envconfig)

    def test_make_pod_envconfig_wrong_auth_backend(self) -> NoReturn:
        """Teting make pod envconfig with wrong auth_backend."""
        config = {
            "enable_test": False,
            "database_commonkey": "commonkey",
            "log_level": "DEBUG",
            "auth_backend": "kerberos",
        }
        relation_state = {
            "message_host": "kafka",
            "message_port": 9090,
            "database_uri": "mongodb://mongo",
            "prometheus_host": "prometheus",
            "prometheus_port": 9082,
            "keystone_host": "keystone",
            "keystone_port": 5000,
            "keystone_user_domain_name": "user_domain",
            "keystone_project_domain_name": "project_domain",
            "keystone_username": "username",
            "keystone_password": "password",
            "keystone_service": "service",
        }

        with self.assertRaises(ValueError) as exc:
            pod_spec._make_pod_envconfig(config, relation_state)

        self.assertTrue(
            "auth_backend needs to be either internal or keystone" in str(exc.exception)
        )

    def test_make_pod_ingress_resources_without_site_url(self) -> NoReturn:
        """Testing make pod ingress resources without site_url."""
        config = {"site_url": ""}
        app_name = "nbi"
        port = 9999

        pod_ingress_resources = pod_spec._make_pod_ingress_resources(
            config, app_name, port
        )

        self.assertIsNone(pod_ingress_resources)

    def test_make_pod_ingress_resources(self) -> NoReturn:
        """Testing make pod ingress resources."""
        config = {
            "site_url": "http://nbi",
            "max_file_size": 0,
            "ingress_whitelist_source_range": "",
        }
        app_name = "nbi"
        port = 9999

        expected_result = [
            {
                "name": f"{app_name}-ingress",
                "annotations": {
                    "nginx.ingress.kubernetes.io/proxy-body-size": f"{config['max_file_size']}",
                    "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
                    "nginx.ingress.kubernetes.io/ssl-redirect": "false",
                },
                "spec": {
                    "rules": [
                        {
                            "host": app_name,
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "backend": {
                                            "serviceName": app_name,
                                            "servicePort": port,
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        ]

        pod_ingress_resources = pod_spec._make_pod_ingress_resources(
            config, app_name, port
        )

        self.assertListEqual(expected_result, pod_ingress_resources)

    def test_make_pod_ingress_resources_with_whitelist_source_range(self) -> NoReturn:
        """Testing make pod ingress resources with whitelist_source_range."""
        config = {
            "site_url": "http://nbi",
            "max_file_size": 0,
            "ingress_whitelist_source_range": "0.0.0.0/0",
        }
        app_name = "nbi"
        port = 9999

        expected_result = [
            {
                "name": f"{app_name}-ingress",
                "annotations": {
                    "nginx.ingress.kubernetes.io/proxy-body-size": f"{config['max_file_size']}",
                    "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
                    "nginx.ingress.kubernetes.io/ssl-redirect": "false",
                    "nginx.ingress.kubernetes.io/whitelist-source-range": config[
                        "ingress_whitelist_source_range"
                    ],
                },
                "spec": {
                    "rules": [
                        {
                            "host": app_name,
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "backend": {
                                            "serviceName": app_name,
                                            "servicePort": port,
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        ]

        pod_ingress_resources = pod_spec._make_pod_ingress_resources(
            config, app_name, port
        )

        self.assertListEqual(expected_result, pod_ingress_resources)

    def test_make_pod_ingress_resources_with_https(self) -> NoReturn:
        """Testing make pod ingress resources with HTTPs."""
        config = {
            "site_url": "https://nbi",
            "max_file_size": 0,
            "ingress_whitelist_source_range": "",
            "tls_secret_name": "",
        }
        app_name = "nbi"
        port = 9999

        expected_result = [
            {
                "name": f"{app_name}-ingress",
                "annotations": {
                    "nginx.ingress.kubernetes.io/proxy-body-size": f"{config['max_file_size']}",
                    "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
                },
                "spec": {
                    "rules": [
                        {
                            "host": app_name,
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "backend": {
                                            "serviceName": app_name,
                                            "servicePort": port,
                                        },
                                    }
                                ]
                            },
                        }
                    ],
                    "tls": [{"hosts": [app_name]}],
                },
            }
        ]

        pod_ingress_resources = pod_spec._make_pod_ingress_resources(
            config, app_name, port
        )

        self.assertListEqual(expected_result, pod_ingress_resources)

    def test_make_pod_ingress_resources_with_https_tls_secret_name(self) -> NoReturn:
        """Testing make pod ingress resources with HTTPs and TLS secret name."""
        config = {
            "site_url": "https://nbi",
            "max_file_size": 0,
            "ingress_whitelist_source_range": "",
            "tls_secret_name": "secret_name",
        }
        app_name = "nbi"
        port = 9999

        expected_result = [
            {
                "name": f"{app_name}-ingress",
                "annotations": {
                    "nginx.ingress.kubernetes.io/proxy-body-size": f"{config['max_file_size']}",
                    "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
                },
                "spec": {
                    "rules": [
                        {
                            "host": app_name,
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "backend": {
                                            "serviceName": app_name,
                                            "servicePort": port,
                                        },
                                    }
                                ]
                            },
                        }
                    ],
                    "tls": [
                        {"hosts": [app_name], "secretName": config["tls_secret_name"]}
                    ],
                },
            }
        ]

        pod_ingress_resources = pod_spec._make_pod_ingress_resources(
            config, app_name, port
        )

        self.assertListEqual(expected_result, pod_ingress_resources)

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

    def test_make_pod_spec_without_image_info(self) -> NoReturn:
        """Testing make pod spec without image_info."""
        image_info = None
        config = {
            "enable_test": False,
            "database_commonkey": "commonkey",
            "log_level": "DEBUG",
            "auth_backend": "internal",
            "site_url": "",
        }
        relation_state = {
            "message_host": "kafka",
            "message_port": 9090,
            "database_uri": "mongodb://mongo",
            "prometheus_host": "prometheus",
            "prometheus_port": 9082,
        }
        app_name = "nbi"
        port = 9999

        spec = pod_spec.make_pod_spec(
            image_info, config, relation_state, app_name, port
        )

        self.assertIsNone(spec)

    def test_make_pod_spec_without_config(self) -> NoReturn:
        """Testing make pod spec without config."""
        image_info = {"upstream-source": "opensourcemano/nbi:8"}
        config = {}
        relation_state = {
            "message_host": "kafka",
            "message_port": 9090,
            "database_uri": "mongodb://mongo",
            "prometheus_host": "prometheus",
            "prometheus_port": 9082,
        }
        app_name = "nbi"
        port = 9999

        with self.assertRaises(ValueError):
            pod_spec.make_pod_spec(image_info, config, relation_state, app_name, port)

    def test_make_pod_spec_without_relation_state(self) -> NoReturn:
        """Testing make pod spec without relation_state."""
        image_info = {"upstream-source": "opensourcemano/nbi:8"}
        config = {
            "enable_test": False,
            "database_commonkey": "commonkey",
            "log_level": "DEBUG",
            "auth_backend": "internal",
            "site_url": "",
        }
        relation_state = {}
        app_name = "nbi"
        port = 9999

        with self.assertRaises(ValueError):
            pod_spec.make_pod_spec(image_info, config, relation_state, app_name, port)

    def test_make_pod_spec(self) -> NoReturn:
        """Testing make pod spec."""
        image_info = {"upstream-source": "opensourcemano/nbi:8"}
        config = {
            "enable_test": False,
            "database_commonkey": "commonkey",
            "log_level": "DEBUG",
            "auth_backend": "internal",
            "site_url": "",
        }
        relation_state = {
            "message_host": "kafka",
            "message_port": 9090,
            "database_uri": "mongodb://mongo",
            "prometheus_host": "prometheus",
            "prometheus_port": 9082,
        }
        app_name = "nbi"
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
                            "name": "nbi",
                            "containerPort": port,
                            "protocol": "TCP",
                        }
                    ],
                    "envConfig": {
                        "ALLOW_ANONYMOUS_LOGIN": "yes",
                        "OSMNBI_SERVER_ENABLE_TEST": config["enable_test"],
                        "OSMNBI_STATIC_DIR": "/app/osm_nbi/html_public",
                        "OSMNBI_MESSAGE_HOST": relation_state["message_host"],
                        "OSMNBI_MESSAGE_DRIVER": "kafka",
                        "OSMNBI_MESSAGE_PORT": relation_state["message_port"],
                        "OSMNBI_DATABASE_DRIVER": "mongo",
                        "OSMNBI_DATABASE_URI": relation_state["database_uri"],
                        "OSMNBI_DATABASE_COMMONKEY": config["database_commonkey"],
                        "OSMNBI_STORAGE_DRIVER": "mongo",
                        "OSMNBI_STORAGE_PATH": "/app/storage",
                        "OSMNBI_STORAGE_COLLECTION": "files",
                        "OSMNBI_STORAGE_URI": relation_state["database_uri"],
                        "OSMNBI_PROMETHEUS_HOST": relation_state["prometheus_host"],
                        "OSMNBI_PROMETHEUS_PORT": relation_state["prometheus_port"],
                        "OSMNBI_LOG_LEVEL": config["log_level"],
                        "OSMNBI_AUTHENTICATION_BACKEND": config["auth_backend"],
                    },
                }
            ],
            "kubernetesResources": {
                "ingressResources": [],
            },
        }

        spec = pod_spec.make_pod_spec(
            image_info, config, relation_state, app_name, port
        )

        self.assertDictEqual(expected_result, spec)

    def test_make_pod_spec_with_keystone(self) -> NoReturn:
        """Testing make pod spec with keystone."""
        image_info = {"upstream-source": "opensourcemano/nbi:8"}
        config = {
            "enable_test": False,
            "database_commonkey": "commonkey",
            "log_level": "DEBUG",
            "auth_backend": "keystone",
            "site_url": "",
        }
        relation_state = {
            "message_host": "kafka",
            "message_port": 9090,
            "database_uri": "mongodb://mongo",
            "prometheus_host": "prometheus",
            "prometheus_port": 9082,
            "keystone_host": "keystone",
            "keystone_port": 5000,
            "keystone_user_domain_name": "user_domain",
            "keystone_project_domain_name": "project_domain",
            "keystone_username": "username",
            "keystone_password": "password",
            "keystone_service": "service",
        }
        app_name = "nbi"
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
                            "name": "nbi",
                            "containerPort": port,
                            "protocol": "TCP",
                        }
                    ],
                    "envConfig": {
                        "ALLOW_ANONYMOUS_LOGIN": "yes",
                        "OSMNBI_SERVER_ENABLE_TEST": config["enable_test"],
                        "OSMNBI_STATIC_DIR": "/app/osm_nbi/html_public",
                        "OSMNBI_MESSAGE_HOST": relation_state["message_host"],
                        "OSMNBI_MESSAGE_DRIVER": "kafka",
                        "OSMNBI_MESSAGE_PORT": relation_state["message_port"],
                        "OSMNBI_DATABASE_DRIVER": "mongo",
                        "OSMNBI_DATABASE_URI": relation_state["database_uri"],
                        "OSMNBI_DATABASE_COMMONKEY": config["database_commonkey"],
                        "OSMNBI_STORAGE_DRIVER": "mongo",
                        "OSMNBI_STORAGE_PATH": "/app/storage",
                        "OSMNBI_STORAGE_COLLECTION": "files",
                        "OSMNBI_STORAGE_URI": relation_state["database_uri"],
                        "OSMNBI_PROMETHEUS_HOST": relation_state["prometheus_host"],
                        "OSMNBI_PROMETHEUS_PORT": relation_state["prometheus_port"],
                        "OSMNBI_LOG_LEVEL": config["log_level"],
                        "OSMNBI_AUTHENTICATION_BACKEND": config["auth_backend"],
                        "OSMNBI_AUTHENTICATION_AUTH_URL": relation_state[
                            "keystone_host"
                        ],
                        "OSMNBI_AUTHENTICATION_AUTH_PORT": relation_state[
                            "keystone_port"
                        ],
                        "OSMNBI_AUTHENTICATION_USER_DOMAIN_NAME": relation_state[
                            "keystone_user_domain_name"
                        ],
                        "OSMNBI_AUTHENTICATION_PROJECT_DOMAIN_NAME": relation_state[
                            "keystone_project_domain_name"
                        ],
                        "OSMNBI_AUTHENTICATION_SERVICE_USERNAME": relation_state[
                            "keystone_username"
                        ],
                        "OSMNBI_AUTHENTICATION_SERVICE_PASSWORD": relation_state[
                            "keystone_password"
                        ],
                        "OSMNBI_AUTHENTICATION_SERVICE_PROJECT": relation_state[
                            "keystone_service"
                        ],
                    },
                }
            ],
            "kubernetesResources": {
                "ingressResources": [],
            },
        }

        spec = pod_spec.make_pod_spec(
            image_info, config, relation_state, app_name, port
        )

        self.assertDictEqual(expected_result, spec)


if __name__ == "__main__":
    unittest.main()
