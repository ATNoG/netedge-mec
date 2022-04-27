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

from ipaddress import ip_network
from typing import Any, Callable, Dict, List, NoReturn
from urllib.parse import urlparse


def _validate_max_file_size(max_file_size: int, site_url: str) -> bool:
    """Validate max_file_size.

    Args:
        max_file_size (int): maximum file size allowed.
        site_url (str): endpoint url.

    Returns:
        bool: True if valid, false otherwise.
    """
    if not site_url:
        return True

    parsed = urlparse(site_url)

    if not parsed.scheme.startswith("http"):
        return True

    if max_file_size is None:
        return False

    return max_file_size >= 0


def _validate_ip_network(network: str) -> bool:
    """Validate IP network.

    Args:
        network (str): IP network range.

    Returns:
        bool: True if valid, false otherwise.
    """
    if not network:
        return True

    try:
        ip_network(network)
    except ValueError:
        return False

    return True


def _validate_keystone_config(keystone: bool, value: Any, validator: Callable) -> bool:
    """Validate keystone configurations.

    Args:
        keystone (bool): is keystone enabled, true if so, false otherwise.
        value (Any): value to be validated.
        validator (Callable): function to validate configuration.

    Returns:
        bool: true if valid, false otherwise.
    """
    if not keystone:
        return True

    return validator(value)


def _validate_data(
    config_data: Dict[str, Any], relation_data: Dict[str, Any], keystone: bool
) -> NoReturn:
    """Validate input data.

    Args:
        config_data (Dict[str, Any]): configuration data.
        relation_data (Dict[str, Any]): relation data.
        keystone (bool): is keystone to be used.
    """
    config_validators = {
        "enable_test": lambda value, _: isinstance(value, bool),
        "database_commonkey": lambda value, _: (
            isinstance(value, str) and len(value) > 1
        ),
        "log_level": lambda value, _: (
            isinstance(value, str) and value in ("INFO", "DEBUG")
        ),
        "auth_backend": lambda value, _: (
            isinstance(value, str) and (value == "internal" or value == "keystone")
        ),
        "site_url": lambda value, _: isinstance(value, str)
        if value is not None
        else True,
        "max_file_size": lambda value, values: _validate_max_file_size(
            value, values.get("site_url")
        ),
        "ingress_whitelist_source_range": lambda value, _: _validate_ip_network(value),
        "tls_secret_name": lambda value, _: isinstance(value, str)
        if value is not None
        else True,
    }
    relation_validators = {
        "message_host": lambda value, _: isinstance(value, str),
        "message_port": lambda value, _: isinstance(value, int) and value > 0,
        "database_uri": lambda value, _: (
            isinstance(value, str) and value.startswith("mongodb://")
        ),
        "prometheus_host": lambda value, _: isinstance(value, str),
        "prometheus_port": lambda value, _: isinstance(value, int) and value > 0,
        "keystone_host": lambda value, _: _validate_keystone_config(
            keystone, value, lambda x: isinstance(x, str) and len(x) > 0
        ),
        "keystone_port": lambda value, _: _validate_keystone_config(
            keystone, value, lambda x: isinstance(x, int) and x > 0
        ),
        "keystone_user_domain_name": lambda value, _: _validate_keystone_config(
            keystone, value, lambda x: isinstance(x, str) and len(x) > 0
        ),
        "keystone_project_domain_name": lambda value, _: _validate_keystone_config(
            keystone, value, lambda x: isinstance(x, str) and len(x) > 0
        ),
        "keystone_username": lambda value, _: _validate_keystone_config(
            keystone, value, lambda x: isinstance(x, str) and len(x) > 0
        ),
        "keystone_password": lambda value, _: _validate_keystone_config(
            keystone, value, lambda x: isinstance(x, str) and len(x) > 0
        ),
        "keystone_service": lambda value, _: _validate_keystone_config(
            keystone, value, lambda x: isinstance(x, str) and len(x) > 0
        ),
    }
    problems = []

    for key, validator in config_validators.items():
        valid = validator(config_data.get(key), config_data)

        if not valid:
            problems.append(key)

    for key, validator in relation_validators.items():
        valid = validator(relation_data.get(key), relation_data)

        if not valid:
            problems.append(key)

    if len(problems) > 0:
        raise ValueError("Errors found in: {}".format(", ".join(problems)))


def _make_pod_ports(port: int) -> List[Dict[str, Any]]:
    """Generate pod ports details.

    Args:
        port (int): port to expose.

    Returns:
        List[Dict[str, Any]]: pod port details.
    """
    return [{"name": "nbi", "containerPort": port, "protocol": "TCP"}]


def _make_pod_envconfig(
    config: Dict[str, Any], relation_state: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate pod environment configuration.

    Args:
        config (Dict[str, Any]): configuration information.
        relation_state (Dict[str, Any]): relation state information.

    Returns:
        Dict[str, Any]: pod environment configuration.
    """
    envconfig = {
        # General configuration
        "ALLOW_ANONYMOUS_LOGIN": "yes",
        "OSMNBI_SERVER_ENABLE_TEST": config["enable_test"],
        "OSMNBI_STATIC_DIR": "/app/osm_nbi/html_public",
        # Kafka configuration
        "OSMNBI_MESSAGE_HOST": relation_state["message_host"],
        "OSMNBI_MESSAGE_DRIVER": "kafka",
        "OSMNBI_MESSAGE_PORT": relation_state["message_port"],
        # Database configuration
        "OSMNBI_DATABASE_DRIVER": "mongo",
        "OSMNBI_DATABASE_URI": relation_state["database_uri"],
        "OSMNBI_DATABASE_COMMONKEY": config["database_commonkey"],
        # Storage configuration
        "OSMNBI_STORAGE_DRIVER": "mongo",
        "OSMNBI_STORAGE_PATH": "/app/storage",
        "OSMNBI_STORAGE_COLLECTION": "files",
        "OSMNBI_STORAGE_URI": relation_state["database_uri"],
        # Prometheus configuration
        "OSMNBI_PROMETHEUS_HOST": relation_state["prometheus_host"],
        "OSMNBI_PROMETHEUS_PORT": relation_state["prometheus_port"],
        # Log configuration
        "OSMNBI_LOG_LEVEL": config["log_level"],
    }

    if config["auth_backend"] == "internal":
        envconfig["OSMNBI_AUTHENTICATION_BACKEND"] = "internal"
    elif config["auth_backend"] == "keystone":
        envconfig.update(
            {
                "OSMNBI_AUTHENTICATION_BACKEND": "keystone",
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
                "OSMNBI_AUTHENTICATION_SERVICE_PROJECT": relation_state[
                    "keystone_service"
                ],
            }
        )
    else:
        raise ValueError("auth_backend needs to be either internal or keystone")

    return envconfig


def _make_pod_ingress_resources(
    config: Dict[str, Any], app_name: str, port: int
) -> List[Dict[str, Any]]:
    """Generate pod ingress resources.

    Args:
        config (Dict[str, Any]): configuration information.
        app_name (str): application name.
        port (int): port to expose.

    Returns:
        List[Dict[str, Any]]: pod ingress resources.
    """
    site_url = config.get("site_url")

    if not site_url:
        return

    parsed = urlparse(site_url)

    if not parsed.scheme.startswith("http"):
        return

    max_file_size = config["max_file_size"]
    ingress_whitelist_source_range = config["ingress_whitelist_source_range"]

    annotations = {
        "nginx.ingress.kubernetes.io/proxy-body-size": "{}".format(
            str(max_file_size) + "m" if max_file_size > 0 else max_file_size
        ),
        "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
    }

    if ingress_whitelist_source_range:
        annotations[
            "nginx.ingress.kubernetes.io/whitelist-source-range"
        ] = ingress_whitelist_source_range

    ingress_spec_tls = None

    if parsed.scheme == "https":
        ingress_spec_tls = [{"hosts": [parsed.hostname]}]
        tls_secret_name = config["tls_secret_name"]
        if tls_secret_name:
            ingress_spec_tls[0]["secretName"] = tls_secret_name
    else:
        annotations["nginx.ingress.kubernetes.io/ssl-redirect"] = "false"

    ingress = {
        "name": "{}-ingress".format(app_name),
        "annotations": annotations,
        "spec": {
            "rules": [
                {
                    "host": parsed.hostname,
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
    if ingress_spec_tls:
        ingress["spec"]["tls"] = ingress_spec_tls

    return [ingress]


def _make_startup_probe() -> Dict[str, Any]:
    """Generate startup probe.

    Returns:
        Dict[str, Any]: startup probe.
    """
    return {
        "exec": {"command": ["/usr/bin/pgrep python3"]},
        "initialDelaySeconds": 60,
        "timeoutSeconds": 5,
    }


def _make_readiness_probe(port: int) -> Dict[str, Any]:
    """Generate readiness probe.

    Args:
        port (int): [description]

    Returns:
        Dict[str, Any]: readiness probe.
    """
    return {
        "httpGet": {
            "path": "/osm/",
            "port": port,
        },
        "initialDelaySeconds": 45,
        "timeoutSeconds": 5,
    }


def _make_liveness_probe(port: int) -> Dict[str, Any]:
    """Generate liveness probe.

    Args:
        port (int): [description]

    Returns:
        Dict[str, Any]: liveness probe.
    """
    return {
        "httpGet": {
            "path": "/osm/",
            "port": port,
        },
        "initialDelaySeconds": 45,
        "timeoutSeconds": 5,
    }


def make_pod_spec(
    image_info: Dict[str, str],
    config: Dict[str, Any],
    relation_state: Dict[str, Any],
    app_name: str = "nbi",
    port: int = 9999,
) -> Dict[str, Any]:
    """Generate the pod spec information.

    Args:
        image_info (Dict[str, str]): Object provided by
                                     OCIImageResource("image").fetch().
        config (Dict[str, Any]): Configuration information.
        relation_state (Dict[str, Any]): Relation state information.
        app_name (str, optional): Application name. Defaults to "nbi".
        port (int, optional): Port for the container. Defaults to 9999.

    Returns:
        Dict[str, Any]: Pod spec dictionary for the charm.
    """
    if not image_info:
        return None

    #_validate_data(config, relation_state, config.get("auth_backend") == "keystone")

    ports = _make_pod_ports(port)
    env_config = _make_pod_envconfig(config, relation_state)
    ingress_resources = _make_pod_ingress_resources(config, app_name, port)

    return {
        "version": 3,
        "containers": [
            {
                "name": app_name,
                "imageDetails": image_info,
                "imagePullPolicy": "Always",
                "ports": ports,
                "envConfig": env_config,
            }
        ],
        "kubernetesResources": {
            "ingressResources": ingress_resources or [],
            "services": [
				{
                    "name": app_name,
                    "spec": {
                        "selector": {
                            "app.kubernetes.io/name": app_name
                        },
                        "ports": [
                            {
                                "protocol": "TCP",
                                "port": port,
                                "targetPort": port,
                                "nodePort": port
                            }
                        ],
                        "type": "LoadBalancer",
                    },
                },
			]
        },
    }
