 - Openstack snapshot to image:
    ```bash
    $ openstack --insecure server list
    $ openstack --insecure server image create --name <snapshot_name> <instance_id>
    $ openstack --insecure image list
    $ openstack --insecure image save --file <img_name>.qcow2 <snapshot_id>
    ```
