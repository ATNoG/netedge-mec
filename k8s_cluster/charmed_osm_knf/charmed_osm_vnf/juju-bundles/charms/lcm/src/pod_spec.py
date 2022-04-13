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

import logging
from typing import Any, Dict, List, NoReturn

logger = logging.getLogger(__name__)


def _validate_data(
    config_data: Dict[str, Any], relation_data: Dict[str, Any]
) -> NoReturn:
    """Validate input data.

    Args:
        config_data (Dict[str, Any]): configuration data.
        relation_data (Dict[str, Any]): relation data.
    """
    config_validators = {
        "database_commonkey": lambda value, _: (
            isinstance(value, str) and len(value) > 1
        ),
        "log_level": lambda value, _: (
            isinstance(value, str) and value in ("INFO", "DEBUG")
        ),
        "vca_host": lambda value, _: isinstance(value, str) and len(value) > 1,
        "vca_port": lambda value, _: isinstance(value, int) and value > 0,
        "vca_user": lambda value, _: isinstance(value, str) and len(value) > 1,
        "vca_pubkey": lambda value, _: isinstance(value, str) and len(value) > 1,
        "vca_password": lambda value, _: isinstance(value, str) and len(value) > 1,
        "vca_cacert": lambda value, _: isinstance(value, str),
        "vca_cloud": lambda value, _: isinstance(value, str) and len(value) > 1,
        "vca_k8s_cloud": lambda value, _: isinstance(value, str) and len(value) > 1,
        "vca_apiproxy": lambda value, _: (isinstance(value, str) and len(value) > 1)
        if value
        else True,
    }
    relation_validators = {
        "ro_host": lambda value, _: isinstance(value, str) and len(value) > 1,
        "ro_port": lambda value, _: isinstance(value, int) and value > 0,
        "message_host": lambda value, _: isinstance(value, str) and len(value) > 1,
        "message_port": lambda value, _: isinstance(value, int) and value > 0,
        "database_uri": lambda value, _: isinstance(value, str) and len(value) > 1,
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
    return [{"name": "lcm", "containerPort": port, "protocol": "TCP"}]


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
        "OSMLCM_GLOBAL_LOGLEVEL": config["log_level"],
        # RO configuration
        "OSMLCM_RO_HOST": relation_state["ro_host"],
        "OSMLCM_RO_PORT": relation_state["ro_port"],
        "OSMLCM_RO_TENANT": "osm",
        # Kafka configuration
        "OSMLCM_MESSAGE_DRIVER": "kafka",
        "OSMLCM_MESSAGE_HOST": relation_state["message_host"],
        "OSMLCM_MESSAGE_PORT": relation_state["message_port"],
        # Database configuration
        "OSMLCM_DATABASE_DRIVER": "mongo",
        "OSMLCM_DATABASE_URI": relation_state["database_uri"],
        "OSMLCM_DATABASE_COMMONKEY": config["database_commonkey"],
        # Storage configuration
        "OSMLCM_STORAGE_DRIVER": "mongo",
        "OSMLCM_STORAGE_PATH": "/app/storage",
        "OSMLCM_STORAGE_COLLECTION": "files",
        "OSMLCM_STORAGE_URI": relation_state["database_uri"],
        # VCA configuration
        "OSMLCM_VCA_HOST": config["vca_host"],
        "OSMLCM_VCA_PORT": config["vca_port"],
        "OSMLCM_VCA_USER": config["vca_user"],
        "OSMLCM_VCA_PUBKEY": config["vca_pubkey"],
        "OSMLCM_VCA_SECRET": config["vca_password"],
        "OSMLCM_VCA_CACERT": config["vca_cacert"],
        "OSMLCM_VCA_CLOUD": config["vca_cloud"],
        "OSMLCM_VCA_K8S_CLOUD": config["vca_k8s_cloud"],
    }

    if "vca_apiproxy" in config and config["vca_apiproxy"]:
        envconfig["OSMLCM_VCA_APIPROXY"] = config["vca_apiproxy"]

    return envconfig


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
    app_name: str = "lcm",
    port: int = 9999,
) -> Dict[str, Any]:
    """Generate the pod spec information.

    Args:
        image_info (Dict[str, str]): Object provided by
                                     OCIImageResource("image").fetch().
        config (Dict[str, Any]): Configuration information.
        relation_state (Dict[str, Any]): Relation state information.
        app_name (str, optional): Application name. Defaults to "lcm".
        port (int, optional): Port for the container. Defaults to 9999.

    Returns:
        Dict[str, Any]: Pod spec dictionary for the charm.
    """
    if not image_info:
        return None

    _validate_data(config, relation_state)

    ports = _make_pod_ports(port)
    env_config = _make_pod_envconfig(config, relation_state)

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
            "ingressResources": [],
        },
    }
