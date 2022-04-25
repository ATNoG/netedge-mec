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

# pylint: disable=E0213


from ipaddress import ip_network
import logging
from typing import NoReturn, Optional
from urllib.parse import urlparse


from charms.kafka_k8s.v0.kafka import KafkaEvents, KafkaRequires
from ops.main import main
from opslib.osm.charm import CharmedOsmBase, RelationsMissing
from opslib.osm.interfaces.http import HttpServer
from opslib.osm.interfaces.keystone import KeystoneClient
from opslib.osm.interfaces.mongo import MongoClient
from opslib.osm.interfaces.prometheus import PrometheusClient
from opslib.osm.pod import (
    ContainerV3Builder,
    IngressResourceV3Builder,
    PodRestartPolicy,
    PodSpecV3Builder,
)
from opslib.osm.validator import ModelValidator, validator


logger = logging.getLogger(__name__)

PORT = 9999


class ConfigModel(ModelValidator):
    enable_test: bool
    auth_backend: str
    database_commonkey: str
    log_level: str
    max_file_size: int
    site_url: Optional[str]
    cluster_issuer: Optional[str]
    ingress_class: Optional[str]
    ingress_whitelist_source_range: Optional[str]
    tls_secret_name: Optional[str]
    mongodb_uri: Optional[str]
    image_pull_policy: str
    debug_mode: bool
    security_context: bool

    @validator("auth_backend")
    def validate_auth_backend(cls, v):
        if v not in {"internal", "keystone"}:
            raise ValueError("value must be 'internal' or 'keystone'")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        if v not in {"INFO", "DEBUG"}:
            raise ValueError("value must be INFO or DEBUG")
        return v

    @validator("max_file_size")
    def validate_max_file_size(cls, v):
        if v < 0:
            raise ValueError("value must be equal or greater than 0")
        return v

    @validator("site_url")
    def validate_site_url(cls, v):
        if v:
            parsed = urlparse(v)
            if not parsed.scheme.startswith("http"):
                raise ValueError("value must start with http")
        return v

    @validator("ingress_whitelist_source_range")
    def validate_ingress_whitelist_source_range(cls, v):
        if v:
            ip_network(v)
        return v

    @validator("mongodb_uri")
    def validate_mongodb_uri(cls, v):
        if v and not v.startswith("mongodb://"):
            raise ValueError("mongodb_uri is not properly formed")
        return v

    @validator("image_pull_policy")
    def validate_image_pull_policy(cls, v):
        values = {
            "always": "Always",
            "ifnotpresent": "IfNotPresent",
            "never": "Never",
        }
        v = v.lower()
        if v not in values.keys():
            raise ValueError("value must be always, ifnotpresent or never")
        return values[v]


class NbiCharm(CharmedOsmBase):

    on = KafkaEvents()

    def __init__(self, *args) -> NoReturn:
        super().__init__(
            *args,
            oci_image="image",
            vscode_workspace=VSCODE_WORKSPACE,
        )
        if self.config.get("debug_mode"):
            self.enable_debug_mode(
                pubkey=self.config.get("debug_pubkey"),
                hostpaths={
                    "NBI": {
                        "hostpath": self.config.get("debug_nbi_local_path"),
                        "container-path": "/usr/lib/python3/dist-packages/osm_nbi",
                    },
                    "osm_common": {
                        "hostpath": self.config.get("debug_common_local_path"),
                        "container-path": "/usr/lib/python3/dist-packages/osm_common",
                    },
                },
            )

        self.kafka = KafkaRequires(self)
        self.framework.observe(self.on.kafka_available, self.configure_pod)
        self.framework.observe(self.on.kafka_broken, self.configure_pod)

        self.mongodb_client = MongoClient(self, "mongodb")
        self.framework.observe(self.on["mongodb"].relation_changed, self.configure_pod)
        self.framework.observe(self.on["mongodb"].relation_broken, self.configure_pod)

        self.prometheus_client = PrometheusClient(self, "prometheus")
        self.framework.observe(
            self.on["prometheus"].relation_changed, self.configure_pod
        )
        self.framework.observe(
            self.on["prometheus"].relation_broken, self.configure_pod
        )

        self.keystone_client = KeystoneClient(self, "keystone")
        self.framework.observe(self.on["keystone"].relation_changed, self.configure_pod)
        self.framework.observe(self.on["keystone"].relation_broken, self.configure_pod)

        self.http_server = HttpServer(self, "nbi")
        self.framework.observe(self.on["nbi"].relation_joined, self._publish_nbi_info)

    def _publish_nbi_info(self, event):
        """Publishes NBI information.

        Args:
            event (EventBase): RO relation event.
        """
        if self.unit.is_leader():
            self.http_server.publish_info(self.app.name, PORT)

    def _check_missing_dependencies(self, config: ConfigModel):
        missing_relations = []

        if not self.kafka.host or not self.kafka.port:
            missing_relations.append("kafka")
        if not config.mongodb_uri and self.mongodb_client.is_missing_data_in_unit():
            missing_relations.append("mongodb")
        if self.prometheus_client.is_missing_data_in_app():
            missing_relations.append("prometheus")
        if config.auth_backend == "keystone":
            if self.keystone_client.is_missing_data_in_app():
                missing_relations.append("keystone")

        if missing_relations:
            raise RelationsMissing(missing_relations)

    def build_pod_spec(self, image_info):
        # Validate config
        config = ConfigModel(**dict(self.config))

        if config.mongodb_uri and not self.mongodb_client.is_missing_data_in_unit():
            raise Exception("Mongodb data cannot be provided via config and relation")

        # Check relations
        self._check_missing_dependencies(config)

        security_context_enabled = (
            config.security_context if not config.debug_mode else False
        )

        # Create Builder for the PodSpec
        pod_spec_builder = PodSpecV3Builder(
            enable_security_context=security_context_enabled
        )

        # Add secrets to the pod
        mongodb_secret_name = f"{self.app.name}-mongodb-secret"
        pod_spec_builder.add_secret(
            mongodb_secret_name,
            {
                "uri": config.mongodb_uri or self.mongodb_client.connection_string,
                "commonkey": config.database_commonkey,
            },
        )

        # Build Init Container
        pod_spec_builder.add_init_container(
            {
                "name": "init-check",
                "image": "alpine:latest",
                "command": [
                    "sh",
                    "-c",
                    f"until (nc -zvw1 {self.kafka.host} {self.kafka.port} ); do sleep 3; done; exit 0",
                ],
            }
        )

        # Build Container
        container_builder = ContainerV3Builder(
            self.app.name,
            image_info,
            config.image_pull_policy,
            run_as_non_root=security_context_enabled,
        )
        container_builder.add_port(name=self.app.name, port=PORT)
        container_builder.add_tcpsocket_readiness_probe(
            PORT,
            initial_delay_seconds=5,
            timeout_seconds=5,
        )
        container_builder.add_tcpsocket_liveness_probe(
            PORT,
            initial_delay_seconds=45,
            timeout_seconds=10,
        )
        container_builder.add_envs(
            {
                # General configuration
                "ALLOW_ANONYMOUS_LOGIN": "yes",
                "OSMNBI_SERVER_ENABLE_TEST": config.enable_test,
                "OSMNBI_STATIC_DIR": "/app/osm_nbi/html_public",
                # Kafka configuration
                "OSMNBI_MESSAGE_HOST": self.kafka.host,
                "OSMNBI_MESSAGE_DRIVER": "kafka",
                "OSMNBI_MESSAGE_PORT": self.kafka.port,
                # Database configuration
                "OSMNBI_DATABASE_DRIVER": "mongo",
                # Storage configuration
                "OSMNBI_STORAGE_DRIVER": "mongo",
                "OSMNBI_STORAGE_PATH": "/app/storage",
                "OSMNBI_STORAGE_COLLECTION": "files",
                # Prometheus configuration
                "OSMNBI_PROMETHEUS_HOST": self.prometheus_client.hostname,
                "OSMNBI_PROMETHEUS_PORT": self.prometheus_client.port,
                # Log configuration
                "OSMNBI_LOG_LEVEL": config.log_level,
            }
        )
        container_builder.add_secret_envs(
            secret_name=mongodb_secret_name,
            envs={
                "OSMNBI_DATABASE_URI": "uri",
                "OSMNBI_DATABASE_COMMONKEY": "commonkey",
                "OSMNBI_STORAGE_URI": "uri",
            },
        )
        if config.auth_backend == "internal":
            container_builder.add_env("OSMNBI_AUTHENTICATION_BACKEND", "internal")
        elif config.auth_backend == "keystone":
            keystone_secret_name = f"{self.app.name}-keystone-secret"
            pod_spec_builder.add_secret(
                keystone_secret_name,
                {
                    "url": self.keystone_client.host,
                    "port": self.keystone_client.port,
                    "user_domain": self.keystone_client.user_domain_name,
                    "project_domain": self.keystone_client.project_domain_name,
                    "service_username": self.keystone_client.username,
                    "service_password": self.keystone_client.password,
                    "service_project": self.keystone_client.service,
                },
            )
            container_builder.add_env("OSMNBI_AUTHENTICATION_BACKEND", "keystone")
            container_builder.add_secret_envs(
                secret_name=keystone_secret_name,
                envs={
                    "OSMNBI_AUTHENTICATION_AUTH_URL": "url",
                    "OSMNBI_AUTHENTICATION_AUTH_PORT": "port",
                    "OSMNBI_AUTHENTICATION_USER_DOMAIN_NAME": "user_domain",
                    "OSMNBI_AUTHENTICATION_PROJECT_DOMAIN_NAME": "project_domain",
                    "OSMNBI_AUTHENTICATION_SERVICE_USERNAME": "service_username",
                    "OSMNBI_AUTHENTICATION_SERVICE_PASSWORD": "service_password",
                    "OSMNBI_AUTHENTICATION_SERVICE_PROJECT": "service_project",
                },
            )
        container = container_builder.build()

        # Add container to pod spec
        pod_spec_builder.add_container(container)

        # Add ingress resources to pod spec if site url exists
        if config.site_url:
            parsed = urlparse(config.site_url)
            annotations = {
                "nginx.ingress.kubernetes.io/proxy-body-size": "{}".format(
                    str(config.max_file_size) + "m"
                    if config.max_file_size > 0
                    else config.max_file_size
                ),
                "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
            }
            if config.ingress_class:
                annotations["kubernetes.io/ingress.class"] = config.ingress_class
            ingress_resource_builder = IngressResourceV3Builder(
                f"{self.app.name}-ingress", annotations
            )

            if config.ingress_whitelist_source_range:
                annotations[
                    "nginx.ingress.kubernetes.io/whitelist-source-range"
                ] = config.ingress_whitelist_source_range

            if config.cluster_issuer:
                annotations["cert-manager.io/cluster-issuer"] = config.cluster_issuer

            if parsed.scheme == "https":
                ingress_resource_builder.add_tls(
                    [parsed.hostname], config.tls_secret_name
                )
            else:
                annotations["nginx.ingress.kubernetes.io/ssl-redirect"] = "false"

            ingress_resource_builder.add_rule(parsed.hostname, self.app.name, PORT)
            ingress_resource = ingress_resource_builder.build()
            pod_spec_builder.add_ingress_resource(ingress_resource)

        # Add restart policy
        restart_policy = PodRestartPolicy()
        restart_policy.add_secrets()
        pod_spec_builder.set_restart_policy(restart_policy)

        return pod_spec_builder.build()


VSCODE_WORKSPACE = {
    "folders": [
        {"path": "/usr/lib/python3/dist-packages/osm_nbi"},
        {"path": "/usr/lib/python3/dist-packages/osm_common"},
        {"path": "/usr/lib/python3/dist-packages/osm_im"},
    ],
    "settings": {},
    "launch": {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "NBI",
                "type": "python",
                "request": "launch",
                "module": "osm_nbi.nbi",
                "justMyCode": False,
            }
        ],
    },
}


if __name__ == "__main__":
    main(NbiCharm)
