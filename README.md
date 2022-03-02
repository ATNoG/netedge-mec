# mec_nfv
MEC integration with NFVs using OSM


## Charm creation

 - According to the OSM documentation [Day 1: VNF Services Initialization](https://osm.etsi.org/docs/vnf-onboarding-guidelines/03-day1.html), the script `charm_create.sh` creates a sample Juju charm according to the given framework. To more easily use this script system-wide, we advise copying it to the home directory, for instance to the directory `~/.bash_scripts`, and adding an alias to the .bashrc:
    ```bash
    alias charm_create="sh ~/.bash_scripts/charm_create.sh"
    ```
 
 - Then, to create a new charm (on the `charm` directory), you just have to run the command:
    ```bash
    $ charm_create <charm_name>
    ```


## Juju controller (local)

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

```bash
$ juju bootstrap localhost default
```
