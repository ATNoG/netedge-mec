# mec_nfv
MEC integration with NFVs using OSM


## Charm creation

 - According to the OSM documentation [Day 1: VNF Services Initialization](https://osm.etsi.org/docs/vnf-onboarding-guidelines/03-day1.html), the script `charm_create.sh` creates a sample Juju charm according to the given framework. To more easily use this script system wide, we advise to copy it to the home directory, for instance to the directory `~/.bash_scripts`, and add an alias to the .bashrc:
    ```bash
    alias charm_create="sh ~/.bash_scripts/charm_create.sh"
    ```
 
 - Then, to create a new charm (on the `charm` directory), you just have to run the command:
    ```bash
    $ charm_create <charm_name>
    ```
