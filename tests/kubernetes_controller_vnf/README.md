# Create the Kubernetes master VNF with Juju charms

## Create the VNF base descriptor and base charm

 - VNF base descriptor:
	 ```bash
	 $ osm package-create --base-directory k8s_controller vnf k8s_controller
	 ```

 - Create the base charm on the `Scripts/charms` directory:
	 ```bash
	 $ charm_create k8s_controller_installer
	 ```

## Create, build and launch the charm, in order to test it
 
 - Follow the [tutorial](https://www.youtube.com/watch?v=TVNSCDdSj-E&t=294s). 

 - To build the charm, you can run the command:
	 ```
	 $ charmcraft build
	 ```
 - To launch it, you need to access a Juju controller. Then, on the directory `Scripts/charms/k8s_controller_installer`, run the following commands:
	 ```bash
	 # To launch the Juju proxy charm
	 $ juju deploy ./k8s-controller-installer_ubuntu-20.04-amd64.charm --config local-config.yaml

	 # Check the charm deployment status
	 $ watch juju status

	 # Verify the charm logs
	 $ juju debug-log
	 ```

	 - To run the first command, you need to set the local configurations to access the external VM(s) i.e., the host name, username and password of the VM where you will run the commands defined on your Juju charm. A proper example of the contents of such file would be:
	 	 ```yaml
		  k8s-controller-installer:
  		  	 ssh-hostname: 10.0.13.1
  		  	 ssh-username: ubuntu
  		  	 ssh-password: password
		 ```
		 - These properties will then be setted as the ones defined on the charm's configurations, defined by the file `config.yaml`.

### Rebuild a charm

 - During the charm development, it is expected that the developer removes the previous charm deployment and deploy a new one, to test it. Therefore, the following commands are or may be necessary:
	 ```bash
	 # Remove the previous charm deployment
	 $ juju remove-application k8s-controller-installer			# it may be necessary to use the flag --force, if the charm is not removed

	 # Verify when the charm is removed
	 $ watch juju status

	 # Sometimes, it is a good idea to clean the charmcraft cache, because in some cases, it tends to use old files versions, that where in the meanwhile updated
	 $ charmcraft clean
	 ```

	 - After these commands were executed, you just need to run the first set of commands introduced in the main section.
