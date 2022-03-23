from charm import SampleProxyCharm
from lib.charms.osm.sshproxy import FrameworkMock


class Event():
    def __init__(self) -> None:
        self.params = {
            'ip': '1.1.1.1',
            'host': 'controller',
            'port': 1,
            'token': 'ola',
            'cert': 'adeus'
        }
        
proxy_test = SampleProxyCharm(FrameworkMock(), None)

# print("Deploy controller")
# proxy_test.on_deploy_k8s_controller(Event())
# 
# print("\n\n\nDeploy workers")
# proxy_test.on_deploy_k8s_workers(Event())
# 
# print("\n\n\nObtain controller info")
# proxy_test.on_get_k8s_controller_info(Event())
# 
# print("\n\n\nJoin workers")
# proxy_test.on_join_k8s_workers(Event())

print("Add K8s cluster to OSM")
proxy_test.on_add_k8s_cluster_to_osm(Event())
