## When the cloud init is not worker

 - Sometimes, for some random reason, the Openstack might not install our cloud inits, which means that some users we wanted to create to use in our deployments will not be, in fact, created, and we can not use OSM to instantiate our VNFs. For these situations, I built the simple Ansible playbook `init-ansible.yaml`, which creates the users in a similar way I created them using the two cloud-init configurations in this folder. To do so, you will need to set up a few things first:
     1. You will need to install Ansible in your local machine;
     2. You will need to set up the hosts you want to configure. Therefore, you need to edit (or create) the file `/etc/ansible/hosts`. In my case, for the playbook I created, I have the following two types of hosts in this file:
         ```bash
         [controller]
         10.0.13.191
         
         [worker]
         10.0.13.192
         10.0.13.193
         ```
     3. Finally, you just need to execute the playbook, giving it your credentials both for SSH and for executing root commands:
         ```bash
         $ ansible-playbook init-ansible.yaml -u <username> --ask-pass --ask-become-pass
         ```
     - **Note that it is required to have some way to access the referred VMs using SSH (in my case, when this happens, I use an existing Openstack template which allows me to connect to the machine using my LDAP credentials)**
     - **Important note: you should not use this method in production ambients, just for test environments**
