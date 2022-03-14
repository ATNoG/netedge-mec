# NFV MEC
MEC integration with NFVs using OSM (developer documentation)


## Juju and Juju charms

### Setup Juju controller (local)

 - Refs: 
    - [Get started on a localhost](https://juju.is/docs/olm/get-started-on-a-localhost)
 - First, install the necessary snap packages:
    ```bash
    $ sudo snap install juju --classic
    $ sudo snap install charm --classic
    $ sudo snap install charmcraft --classic
    ```

 - Then, you need to configure LXD accordingly:
    ```bash
    # Add your user to the lxd group, and then change the current group ID during login session
    $ sudo adduser $USER lxd
    $ newgrp lxd

    # configure LXD for its environment
    $ lxd init --auto

    # disable IPV6 
    $ lxc network set lxdbr0 ipv6.address none
    ```

    - If the group `lxd` is not present on the machine, first create it, and then restart the `lxd daemon`:
       ```bash
       $ sudo groupadd lxd
       $ sudo systemctl restart snap.lxd.daemon    # or 'sudo systemctl restart lxd' for the debian package
       ```

 - Finally, install the Juju controller on the machine, using the Juju bootstrap process:
    ```bash
    $ juju bootstrap localhost default
    ```

### Create your charm from the default one

 - VNF base descriptor (probably your first sep; **if you already created your VNFD, you should avoid this setp**):
	 ```bash
    $ osm package-create --base-directory <project_directory> vnf <vnf_name>

    # example
	 $ osm package-create --base-directory k8s_cluster vnf k8s_cluster
	 ```

  - According to the OSM documentation [Day 1: VNF Services Initialization](https://osm.etsi.org/docs/vnf-onboarding-guidelines/03-day1.html), the script `charm_create.sh` creates a sample Juju charm according to the given framework. To more easily use this script system-wide, we advise copying it to the home directory, for instance to the directory `~/.bash_scripts`, and adding an alias to the .bashrc:
    ```bash
    alias charm_create="sh ~/.bash_scripts/charm_create.sh"
    ```
 
 - Then, to create a new charm (on the `charm` directory), you just have to run the command:
    ```bash
    $ charm_create <charm_name>

    # example
    $ charm_create k8s_cluster_installer
    ```

 - In the end, you shall have a directory structure similar to the following one:
    ```bash
    ├── <project_directory>                                                                                                                                                       
    │   ├── <vnf_name>_vnf                                                                                                                 
    │   │   ├── charms                                                                                                                      
    │   │   │   └── <charm_name>                                                                                                   
    │   │   │       ├── actions.yaml                                                                                                        
    │   │   │       ├── config.yaml                                                                                                         
    │   │   │       ├── hooks                                                                                                               
    │   │   │       │   ├── install -> ../src/charm.py                                                                                      
    │   │   │       │   ├── start -> ../src/charm.py                   
    │   │   │       │   └── upgrade-charm -> ../src/charm.py                                                                                
    │   │   │       ├── lib                                                                                                                 
    │   │   │       │   ├── charms -> ../mod/charms.osm/charms                                                                              
    │   │   │       │   └── ops -> ../mod/operator/ops                                                                                      
    │   │   │       ├── metadata.yaml                                                                                                       
    │   │   │       ├── mod                                                                                                                 
    │   │   │       │   ├── charms.osm                     
    │   │   │       │   │   ├── charms                                 
    │   │   │       │   │   │   ├── __init__.py                                                                                             
    │   │   │       │   │   │   └── osm                              
    │   │   │       │   │   │       ├── [...]                                                                                         
    │   │   │       │   │   ├── [...]                                 
    │   │   │       │   └── operator
    │   │   │       │       ├── [...]
    │   │   │       │       ├── ops
    │   │   │       │       │   ├── [...]
    │   │   │       ├── src
    │   │   │       │   ├── charm.py
    │   │   │       │   ├── command.py
    │   │   │       │   ├── dependencies.py
    │   │   ├── cloud_init                                          
    │   │   ├── <vnf_name>_vnfd.yaml                            
    │   │   ├── README.md                                      
    │   │   └── Scripts
    │   └── README.md
    └── README.md
    ```

### Test your charms

 - Follow the [tutorial](https://www.youtube.com/watch?v=TVNSCDdSj-E&t=294s).
 - On the machine where you installed the Juju controller, clone your repository (you can add a deployment public key in your repo settings, if you are using Github -- `Settings -> Deploy keys -> Add deploy key`). Then, access the directory where you have created the charm.
 - First, you need to build your charm package:
    ```bash
    $ charmcraft build              # you may need to use this command as root
    ```
 - Then, you need to launch the new charm. To do so, you just have to run the following commands (on the directory corresponding to the charm's name):
    ```bash
    # To launch the Juju proxy charm
    $ juju deploy ./<charm_name>_ubuntu-20.04-amd64.charm --config local-config.yaml                  # if you are not using any configurations, you don't need to use the config flag
    
	 $ juju deploy ./k8s-controller-installer_ubuntu-20.04-amd64.charm --config local-config.yaml      # example

	 # Check the charm deployment status
	 $ watch juju status

	 # Verify the charm logs
	 $ juju debug-log
    ```

    - To run the first command, you may need to pass configurations. For example, you may need to set the local configurations to access the external VM(s) i.e., the host name, username and password of the VM where you will run the commands defined on your Juju charm. A proper example of the contents of such file would be:
	 	 ```yaml
       k8s-cluster-installer:
         ssh-hostname: 10.0.13.1
         ssh-username: ubuntu
         ssh-password: password
		 ```
		 - These properties will then be setted as the ones defined on the charm's configurations, defined by the file `config.yaml`.

### Rebuild a charm

 - During the charm development, it is expected that the developer removes the previous charm deployment and deploy a new one, to test it. Therefore, the following commands are or may be necessary:
	 ```bash
	 # Remove the previous charm deployment
    $ juju remove-application <charm_name>                        # it may be necessary to use the flag --force, if the charm is not removed
	 $ juju remove-application k8s-controller-installer            # example

	 # Verify when the charm is removed
	 $ watch juju status

	 # Sometimes, it is a good idea to clean the charmcraft cache, because in some cases, it tends to use old files versions, that where in the meanwhile updated
	 $ charmcraft clean
	 ```
	 - After these commands are executed, you just need to run the first set of commands introduced in the previous section.

 - Another command that may become handy in some cases, is the following one, which can be used to change the already running charm. Imagine that you did some changes to some charm that you already have executing in your Juju controller: you can apply this changes by just upgrading the charm:
    ```bash
    $ juju upgrade-charm <charm_name> --path ./<path_to_charm_package>/<charm_name>_ubuntu-20.04-amd64.charm

    # example
    $ juju upgrade-charm k8s-cluster-installer --path ./k8s-cluster-installer_ubuntu-20.04-amd64.charm
    ```

    - In most cases, this option can be used instead of the previous one.

### Deploy the same charm package in the same Juju controller more that once, simultaneously

 - Imagine the scenario where you created a multi purpose charm i.e., a charm which can be executed in different ways, with different functionalities, in different environments. An example of such a charm can be found in the directory `k8s_cluster/k8s_cluster_vnf/charms/k8s_cluster_installer/` of this repository, where it can be used for both the installation of a Master k8s node and a Worker k8s node. In this charm, the type of execution can be choosen by parameter, using a local config file, such as:
    ```yaml
    k8s-cluster-installer:
      ssh-hostname: 10.0.13.1
      ssh-username: ubuntu
      ssh-password: password
      entity: controller         # or worker
    ```

 - Therefore, in this example, imagine that I want to deploy the same charm at least two times, one for the Master node (controller) and the other for the worker, in order to test the deployment of a k8s cluster. I can do so the following way:
    ```bash
    # First, I need to build my package
    $ charmcraft build

    # Then, deploy the first charm's application
    $ juju deploy ./<charm_name>_ubuntu-20.04-amd64.charm --config <first_app_config_file>.yaml <first_app_name>
    $ juju deploy ./k8s-cluster-installer_ubuntu-20.04-amd64.charm --config local-config-controller.yaml k8s-controller-installer      # example

    # Finally, deploy the second application
    $ juju deploy ./<charm_name>_ubuntu-20.04-amd64.charm --config <second_app_config_file>.yaml <second_app_name>
    $ juju deploy ./k8s-cluster-installer_ubuntu-20.04-amd64.charm --config local-config-worker.yaml k8s-worker-installer              # example
    
    # Observe that the two apps were deployed
    juju status
    ```

## Creation of the multi-VDU VNF
### How to create a VNF with multiple VDUs

 - To create a VNF with multiple VDUs, you will need to define the different VDUs at the `vnfd:vdu` param level, and `vnfd:df` param level, in the VNFD.
    - At the `vnfd:vdu` param level:
       ```yaml
       vnfd:
         [...]
         vdu:
         - id: controller
           cloud-init-file: cloud-init-controller.cfg
           name: controller
           description: VMs for the Kubernetes' controller plane
           sw-image-desc: "clean-ubuntu"
           virtual-storage-desc:
           - controller-storage
           virtual-compute-desc: controller-compute
           int-cpd:
           - id: controller-int-out
             virtual-network-interface-requirement:
             - name: controller-out
               virtual-interface:
                 type: PARAVIRT
           - id: controller-int-in
             int-virtual-link-desc: internal-vl
             virtual-network-interface-requirement:
             - name: controller-in
               virtual-interface:
                 type: PARAVIRT
         - id: worker
           cloud-init-file: cloud-init-worker.cfg
           name: worker
           description: VMs for the Kubernetes' workers
           sw-image-desc: "clean-ubuntu"
           virtual-storage-desc:
           - worker-storage
           virtual-compute-desc: worker-compute
           int-cpd:
           - id: worker-int-out
             virtual-network-interface-requirement:
             - name: worker-out
               virtual-interface:
                 type: PARAVIRT
           - id: worker-int-in
             int-virtual-link-desc: internal-vl
             virtual-network-interface-requirement:
             - name: worker-in
               virtual-interface:
                 type: PARAVIRT
       ```

       - In this example, it is presented two different VDUs, a controller, and a worker VDU. As seen, they can have different cloud-init configurations, software images, storage configurations and computing configurations. Also, in this example, all the VDUs have two distinct network interfaces, where one of them is to be used as an external interface (i.e., an interface exposed by the corresponding VNF, to be accessed by the NS), and an internal interface (i.e., an interface used in the internal VL of the corresponding VNF, which can be used to interaction between the VDUs of the same VNF, internally). The external interfaces are further described in the `vnfd:ext-cpd` VNF's descriptor. The internal ones, as seen in the above example, have the `int-virtual-link-desc` param, with the value of an existent VL (in this case, the `internal-vl` VL).

    - At the `vnfd:df` param level:
       ```yaml
       vnfd:
         [...]
         df:
         - id: default-df
           instantiation-level:
           - id: default-instantiation-level
             vdu-level:
             - number-of-instances: 1
               vdu-id: controller
             - number-of-instances: 1
               vdu-id: worker
           vdu-profile:
           - id: controller
             min-number-of-instances: 1
             max-number-of-instances: 1
           - id: worker
             min-number-of-instances: 1
             max-number-of-instances: 10
       ```

       - Here, you define the Deployment Flavor (DF). As you may notice, here you define the number of instances of each VDU you previously described in the `vnfd:vdu` param, using the param `number-of-instances`, as well as the minimum and maximum number of instances of each VDU (using the `min-number-of-instances` and the `max-number-of-instances` params, respectively).

### Using VDU-level charms for day-1 and day-2 operations

 - When you have multiple VDUs, with different purposes, you may need to run different charms in each one of them, in order to instantiate the necessary functionalities in a differentiated way in each type of VDU. This can be done using LCM day-1 and day-2 operations at the VDU-level. In order to do this, you need to define this VDU-level charms in your VNFD. Following the used example of the instantiation of a VFS k8s cluster:
    ```yaml
    vnfd:
      [...]
      df:
      - id: default-df
        instantiation-level:
        - id: default-instantiation-level
          vdu-level:
          - number-of-instances: 1
            vdu-id: controller
          - number-of-instances: 1
            vdu-id: worker
        vdu-profile:
        - id: controller
          min-number-of-instances: 1
          max-number-of-instances: 1
        - id: worker
          min-number-of-instances: 1
          max-number-of-instances: 10
        lcm-operations-configuration:
          operate-vnf-op-config:
            day1-2:
            - execution-environment-list:
              - id: controller-ee
                juju:
                  charm: k8s_cluster_installer
                  proxy: true
              id: controller
              initial-config-primitive:
              - execution-environment-ref: controller-ee
                name: config
                parameter:
                - name: ssh-hostname
                  value: <rw_mgmt_ip>
                - name: ssh-username
                  value: <controller_username>
                - name: ssh-password
                  value: <controller_password>
                - name: entity
                  value: controller
                seq: 1
              - execution-environment-ref: controller-ee
                name: deploy-k8s-controller
                parameter:
                - name: vld-cidr
                  value: <vld_cidr>
                seq: 2
              config-primitive:
              - execution-environment-ref: controller-ee
                name: get-k8s-controller-info
              - execution-environment-ref: controller-ee
                name: remove-k8s-worker
                parameter:
                  - name: node
                    data-type: STRING
            - execution-environment-list:
              - id: worker-ee
                juju:
                  charm: k8s_cluster_installer
                  proxy: true
              id: worker
              initial-config-primitive:
              - execution-environment-ref: worker-ee
                name: config
                parameter:
                - name: ssh-hostname
                  value: <rw_mgmt_ip>
                - name: ssh-username
                  value: <worker_username>
                - name: ssh-password
                  value: <worker_password>
                - name: entity
                  value: worker
                seq: 1
              - execution-environment-ref: worker-ee
                name: deploy-k8s-workers
                seq: 2
              config-primitive:
              - execution-environment-ref: worker-ee
                name: join-k8s-workers
                parameter:
                  - name: ip
                    data-type: STRING
                  - name: host
                    data-type: STRING
                  - name: port
                    data-type: INTEGER
                  - name: token
                    data-type: STRING
                  - name: cert
                    data-type: STRING
    ```
    - So, as you may notice, you need to define two distinct execution environment lists, inside the param `vnfd:df:lcm-operations-configuration:operate-vnf-op-config:day1-2`, one for each VDU, in order to have day-1 and day-2 operations differentiated for the two distinct VDUs. Here, the process is somewhat similar to the one used at the VNF-level [day-1](https://osm.etsi.org/docs/vnf-onboarding-guidelines/03-day1.html) and [day-2](https://osm.etsi.org/docs/vnf-onboarding-guidelines/04-day2.html) operations. For each environment list, you need to define at least one Juju charm (in this case, it used the same charm, but with different params, for each VDU) associated to an execution environment reference. Then, you just need to describe the day-1 operations, in the param `initial-config-primitive`, where you may define the order of your actions, as well as the day-2 operations, using the `config-primitive` param, were you can define one or more primitives to be executed at the VDU level (each primitive must correspond to an existing action, defined in your charm actions).

### Launch your NS and corresponding VNFs

 - Having as example the NSD and VNFD defined in the directory `k8s_cluster` in this repository, you may run the following commands to build your NS and VNF packages, and to instantiate a NS, named k8s:
    ```bash
    $ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge nfpkg-create k8s_cluster_vnf
    $ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge nspkg-create k8s_cluster_ns
    $ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge ns-create --ns_name k8s --nsd_name k8s_cluster_nsd --vim_account NETEDGE_MEC           # you can also use the flag config_file, to use a configuration file with some variable configurations (for example, --config_file ns_params.yaml)
    ```

### Execute the VDU primitives previously defined

 - After you instantiate an NS, such as the k8s NS previously described, you may need to run your day-2 primitives. For example, in this specific case, I created a primitive for the controller VDU to obtain the k8s master informations, and other primitive at the VDU k8s worker level, which will execute the necessary commands to join the corresponding workers to the k8s master, using the referred master info. Therefore, I used the OSM client to execute this primitives. Note that the OSM browser GUI also allows you to run these primitives. However, when you have more than one instance of the same VDU deployed, at least in the `OSM 10.0.3`, the interface does not ask you which instance you want to run your primitive on. Therefore, you can use the following commands:
    ```bash
    # Run the controller's primitive (you do not need to define which instance to run on, because there is just one, probably)
    $ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge ns-action k8s --vnf_name 1 --vdu_id controller --action_name get-k8s-controller-info --wait

    # Run the worker's primitive (here, you need to indicate which instance of the VDU you want to run this primitive on; in this case, it was executed on the instance 1, as you may notice)
    $ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge ns-action k8s --vnf_name 1 --vdu_id worker --vdu_count 1 --action_name join-k8s-workers --params_file join_k8s_workers_params.yaml --wait          

    # In order to automate the process of joining multiple worker VDUs at the same time, mainly when you have a lot, you can execute the previous command in a for loop (the loop shown below executes the primitive for the instances 0 to 3)
    for i in {0..3}; do osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge ns-action k8s --vnf_name 1 --vdu_id worker --vdu_count $i --action_name join-k8s-workers --params_file join_k8s_workers_params.yaml --wait; done
    ```
 
### Scaling your VDU

 - Continuing to have this VNF as an example, you may want, for instance, on the go, to scale out (or in) your worker VDU, in order to have a k8s cluster with more workers. To do so, you also need to define the scaling configurations in your VNFD:
    ```yaml
    vnfd:
      [...]
      df:
      - id: default-df
        instantiation-level:
        - id: default-instantiation-level
          vdu-level:
          - number-of-instances: 1
            vdu-id: controller
          - number-of-instances: 1
            vdu-id: worker
          - number-of-instances: 1
            vdu-id: mgmt-VM
        vdu-profile:
        - id: controller
          min-number-of-instances: 1
          max-number-of-instances: 1
        - id: worker
          min-number-of-instances: 1
          max-number-of-instances: 10
        - id: mgmt-VM
          min-number-of-instances: 1
          max-number-of-instances: 1
        scaling-aspect:
        - aspect-delta-details:
            deltas:
            - id: worker-scale-delta
              vdu-delta:
              - id: worker
                number-of-instances: 1      # one instance at each scale operation
          id: worker-scale
          name: worker-scale
          scaling-policy:
          - cooldown-time: 5                # the new instance is created only after 5 seconds from the scale request's was done
            name: manual-worker-scaling
            scaling-type: manual
    ```

    - In this configurations, it was defined the number of instances to deploy (or to remove) with the scaling out operation (or scale in), as well as the VDU were this scaling operation is to be applied (worker VDU) and the minimum time needed to wait until the scale operation is begins (in this case, 5 seconds). It was also defined that this scaling will be triggered manually (through the parameter `scaling-type`).

### Defining the network configurations for the Virtual Link (VL)
