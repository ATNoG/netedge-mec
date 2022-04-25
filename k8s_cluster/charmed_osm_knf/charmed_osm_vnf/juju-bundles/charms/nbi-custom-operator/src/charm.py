#!/usr/bin/env python3
# Copyright 2021 Gabor Meszaros
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import sys
import logging
import requests

sys.path.append("lib")
from ops.charm import ActionEvent, CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    Container,
    MaintenanceStatus,
    WaitingStatus,
)
from ops.pebble import ServiceStatus, PathError

logger = logging.getLogger(__name__)


class NBICustomOperator(CharmBase):
    # StoredState is used to store data the charm needs persisted across invocations.
    _stored = StoredState()

    def __init__(self, *args) -> None:
        super().__init__(*args)

        # Observe charm events
        event_observer_mapping = {
            #self.on.set_creds_action: self._on_set_creds,
            self.on.set_new_vim_action: self._on_set_new_vim,
            self.on.nbi_relation_changed: self._on_nbi_relation_changed,
            #self.on.config_changed: self._on_config_changed,
            #self.on.update_status: self._on_update_status,
            #self.on.restart_action: self._on_restart_action,
            #self.on.start_action: self._on_start_action,
            #self.on.stop_action: self._on_stop_action,
        }
        for event, observer in event_observer_mapping.items():
            self.framework.observe(event, observer)


    #def _on_set_creds(self, event: ActionEvent) -> None:
    #	"""Set the credentials for the NBI."""
    #	creds = event.params.get("creds")
    #	if creds:
    
    
    def _on_set_new_vim(self, event: ActionEvent) -> None:
        msg = "Obtaining new VIM's data..."
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        
        try:
            vim_name = event.params.get("name")
            vim_tenant_name = event.params.get("tenant-name")
            vim_type = event.params.get("type")
            vim_url = event.params.get("url")
            vim_username = event.params.get("username")
            vim_password = event.params.get("password")
            vim_config = {
                event.params.get("project_domain_name"),
                event.params.get("user_domain_name"),
                event.params.get("security_groups"),
                event.params.get("insecure"),
            }
        except Exception as e:
            logger.error(f"Error obtaining the new VIM's data: {e}")
            self.unit.status = BlockedStatus("Couldn't obtain the new VIM's data")
        
        logger.info("CONFIGS: {}".format(event.params.get("configs")))
        logger.info("New VIM: {}".format(self._stored.vim))
        
        msg = "New VIM's data obtained"
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        
        # if there is no NBI data yet, we need to wait for it, storing the relation data
        try:
            nbi_info = self._stored.nbi
        except AttributeError:
            logger.debug("No NBI info stored yet")
            self.unit.status = MaintenanceStatus("Storing the VIM information...")
            
            self._stored.set_default(vim={
                "name": vim_name,
                "tenant-name": vim_tenant_name,
                "type": vim_type,
                "url": vim_url,
                "username": vim_username,
                "password": vim_password,
                "configs": vim_config,
            })
            
            self.unit.status = ActiveStatus("Waiting for NBI")
            return
        
        # then, we need to obtain the authentication token from the NBI
        vim_url = nbi_info.get('url')
        auth_token = self.__authenticate_with_nbi(nbi_url=vim_url, nbi_username=nbi_info.get('username'), 
                                                  nbi_password=nbi_info.get('password'))
        
        # finally, we add the new VIM to the OSM through the NBI
        self.__add_vim_to_osm(nbi_url=vim_url, auth_token=auth_token, vim_name=vim_name, 
                              vim_type=vim_type, vim_url=vim_url, vim_username=vim_username, 
                              vim_password=vim_password, vim_configs=vim_config)
        
    def _on_nbi_relation_changed(self, event: ActionEvent) -> None:
        """Handle relation changes."""

        # first, we need to obtain the relation data
        relation = self.framework.model.get_relation('nbi')
        relation_data = relation.data[relation.app]
        
        nbi_host = relation_data.get('host')
        nbi_port = relation_data.get('port')
        nbi_url = f"{nbi_host}:{nbi_port}"
        
        basic_auth_username = relation_data.get('basic_auth_username')
        basic_auth_password = relation_data.get('basic_auth_password')
        
        nbi_username = basic_auth_username if basic_auth_username and basic_auth_username != 'None' else 'admin'
        nbi_password = basic_auth_password if basic_auth_password and basic_auth_password != 'None' else 'admin'
        
        # if there is no VIM data yet, we need to wait for it, storing the relation data
        try:
            vim_info = self._stored.vim
        except AttributeError:
            logger.debug("No VIM data stored yet")
            self.unit.status = MaintenanceStatus("Storing the NBI information...")
            
            self._stored.set_default(nbi={
                'url': nbi_url,
                'username': nbi_username,
                'password': nbi_password,
            })
            
            self.unit.status = ActiveStatus("Waiting for VIM")
            return

        # then, we need to obtain the authentication token from the NBI
        auth_token = self.__authenticate_with_nbi(nbi_url=nbi_url, nbi_username=nbi_username, nbi_password=nbi_password)
        
        # finally, we add the new VIM to the OSM through the NBI
        self.__add_vim_to_osm(nbi_url=nbi_url, auth_token=auth_token, vim_name=vim_info.get('name'), 
                              vim_type=vim_info.get('type'), vim_url=vim_info.get('url'), vim_username=vim_info.get('username'), 
                              vim_password=vim_info.get('password'), vim_configs=vim_info.get('configs'))
        
        
    def __authenticate_with_nbi(self, nbi_url: str, nbi_username: str, nbi_password: str) -> str:
        msg = "Authenticating with OSM..."
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        try:
            response = requests.post(f"https://{nbi_url}/osm/admin/v1/tokens", json={
                "username": nbi_username,
                "password": nbi_password
            }, headers={
                "Accept": "application/json"
            }, verify=False)
        except Exception as e:
            logger.error(f"Error authenticating with NBI: {e}")
            self.unit.status = BlockedStatus("Couldn't authenticate with NBI")
            raise e
        
        if response.status_code != 200:
            error_info = f"Response with status code: <{response.status_code}>; Response: <{response.json()}>"
            logger.error(error_info)
            self.unit.status = BlockedStatus("Couldn't authenticate with OSM")
            raise Exception(error_info)
        
        msg = "Authenticated with OSM"
        logger.info(msg)
        self.unit.status = ActiveStatus(msg)
        
        return response.json()['id']
    
    def __add_vim_to_osm(self, nbi_url: str, auth_token: str, vim_name: str, vim_type: str, vim_url: str, vim_tenant_name: str, 
                         vim_user: str, vim_password: str, vim_config: dict) -> None:
        msg = "Adding a new VIM to OSM..."
        logger.info(msg)
        self.unit.status = MaintenanceStatus(msg)
        
        try:
            response = requests.post(f"{nbi_url}/osm/admin/v1/vims", json={
                "name": vim_name,
                "description": "Dinamically added VIM",
                "vim_type": vim_type,
                "vim_url": vim_url,
                "vim_tenant_name": vim_tenant_name,
                "vim_user": vim_user,
                "vim_password": vim_password,
                "config": {
                  **vim_config,
                },
            }, headers={
                "Authorization": f"Bearer {auth_token}",
                "Accept": "application/json"
            }, verify=False)
        except Exception as e:
            logger.error(f"Error adding the new VIM: {e}")
            self.unit.status = BlockedStatus("Couldn't add the new VIM")
            raise e

        if response.status_code != 202:
            error_info = f"Response with status code: <{response.status_code}>; Response: <{response.json()}>"
            logger.error(error_info)
            self.unit.status = BlockedStatus("Couldn't add the VIM to OSM")
            raise Exception(error_info)

        msg = "VIM added to OSM with success"
        logger.info(msg)
        self.unit.status = ActiveStatus(msg)

if __name__ == "__main__":
    main(NBICustomOperator)
