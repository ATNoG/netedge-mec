# Create Kubernetes VNF

## Create Kubernetes master VM

 - Follow the instructions in *kubernetes_installation.md*.

## Create Kubernetes master VNF (with only one VDU)

 - First, create a snapshot of the previously created VM;
 - Then, create an image from that snapshot:
    ```bash
    $ openstack --insecure server list
    $ openstack --insecure server image create --name <snapshot_name> <instance_id>    # to create the snapshot of the instance <instance_id>
    $ openstack --insecure image list
    $ openstack --insecure image save --file <img_name>.qcow2 <snapshot_id>
    ```
