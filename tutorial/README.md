# mec_nfv
MEC integration with NFVs using OSM

## Installing OSM
Following the QuickStart guide avaliable at [OSM](https://osm.etsi.org/docs/user-guide/01-quickstart.html)
```sh
wget https://osm-download.etsi.org/ftp/osm-11.0-eleven/install_osm.sh
chmod +x install_osm.sh
./install_osm.sh 2>&1 | tee osm_install_log.txt
```
## Adding VIM to OSM 
Instructions based on [Atnog's documentation](https://atnog-5gaspwiki.av.it.pt/docs/OSM/VimAccountSetup)

Access:
- Dashboard
    - Projects
        - YourUsername
            - VIM Accounts
                - New VIM

In the *New VIM* section, specify your VIM (e.g Openstack,OpenVIM) and add your account and credentials.

Add the connection your VIM Network. This information is available at: 

- API Access 
    - Identity
        - Identity

In *Load Sample Config* load your VIM configuration. 

*Example Config*
```
project_domain_name: 'atnog'
user_domain_name: 'atnog'
insecure: 'true'
security_groups: 'all_open'
```

The security_group *all_open* should exist in the OpenStack Project of the account added previously. This security group should have IP Filter rules that allow your application to function accordinly. 

## Instanciating VNF
Documentation provided in [OSM day 0](https://osm.etsi.org/docs/vnf-onboarding-guidelines/02-day0.html) 
### Create a new vnf package
```
osm package-create --base-directory ~/<package-name> <package-type> <package-name>

osm package-create --base-directory ~/vnf_example vnf vnf_example
```

### Changing the VNF descriptors 
Access the .yaml file inside the package directory which should be lockated in ~/\<package-name\>/\<package-name\>_vnf/\<package-name\>_vnfd.yaml

Change the values accordingly and validate that the sw-image values are correct and available in your VIM.

Add a cloud-init to the yaml to allow connections to the VNF via ssh.

```sh
runcmd:
  - apt update; apt install build-essential; apt install openssh-server
  - systemctl enable --now haveged
  - systemctl enable --now firewalld
  - systemctl enable --now sshd

users:
  - name: controller
    sudo: ['ALL=(ALL) NOPASSWD: ALL']
    groups: users
    ssh-authorized-keys:
      - <ssh public key>
    shell: /bin/bash
    lock_passwd: false
    passwd: <password>

package-upgrade: true

packages:
  - git
  - vim
  - wget
  - bash-completion
  - nmap

power_state:
  mode: reboot
```

### Validating and uploading the VNF package
```
osm nfpkg-create ~/<package-name>/<package-name>_vnf
```

### Creating a new NS package
```
osm package-create --base-directory ~/<package-name> ns <package-name>
```

### Changing the NS descriptors 
Access the .yaml file inside the package directory which should be lockated in ~/\<package-name\>/\<package-name\>_ns/\<package-name\>_nsd.yaml

In this NS descriptors you should, at least, change the virtual-link-desc to the Virtual link network that connects to your VIM Network.

### Validating and uploading the NS package
The difference in NS and VNF package is small so **beware** when creating packages.
NS package creation uses **nspkg-create**, while VNF package creation uses **nfpkg-create**
```
osm nspkg-create ~/<package-name>/<package-name>_vnf
```

### NS Instantiation
```
osm ns-create --ns_name <ns-package-name> --nsd_name <ns-package-name> --vim_account <vim-account-name>
```

