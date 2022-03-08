##### MOCKS #####
class Model():
	def __init__(self,unit):
		self.unit = unit
	config = {
		"tunnel_address": "10.100.100.0/24",
		"tunnel_peer_address": "10.100.100.1/24",
		"listen_port": "51820",
		"save_config": "true",
		"forward_interface": "wg0",
		"ssh-hostname": "10.0.12.107",
		"username": "ubuntu",
		"password": "ubuntu",
		"vsi_id": "1",
	}
class Unit():
	def __init__(self):
		pass
	def is_leader(self):
		return True
class Event():
	params = {}
	def __init__(self):
		pass

	def add_param(self, key, value):
		self.params[key] = value

	def del_param(self, key):
		del self.params[key]

	def set_results(self, x):
		pass
##### END OF MOCKS #####
