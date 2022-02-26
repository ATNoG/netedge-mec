from zmq import proxy
from charm import SampleProxyCharm
from lib.charms.osm.sshproxy import FrameworkMock


proxy_test = SampleProxyCharm(FrameworkMock(), None)
proxy_test.on_deploy_k8s_controller(None)

