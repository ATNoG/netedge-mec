# Create Kubernetes VNF

## Create Kubernetes master VM

 - Create a Ubuntu 20.04 VM, *with no volume attached*;
 - Follow the instructions in *kubernetes_installation.md*.

## Create the VM's image

 - First, create a snapshot of the previously created VM;
 - Then, create an image from that snapshot:
    ```bash
    $ openstack --insecure server list
    $ openstack --insecure server image create --name <snapshot_name> <instance_id>    # to create the snapshot of the instance <instance_id>
    $ openstack --insecure image list
    $ openstack --insecure image save --file <img_name>.qcow2 <snapshot_id>
    ```
 - Finally, upload this new image to the Openstack project and then create the VNF with the image previously created image.


## Create Kubernetes master VNF (with only one VDU)

### Create the VNF and NS descriptors

 - VNF descriptor:
    - First, create the package, and edit the default VNF descriptor (the used one in on the directory `vnf_k8s_master`). Then, validate and upload the VNF package:
       ```bash
       # create the base descriptors
       $ osm package-create --base-directory vnf_k8s_master vnf vnf_k8s_master

       # upload and validate the package to OSM
       $ osm --user netedge --password <password> --project netedge nfpkg-create vnf_k8s_master/vnf_k8s_master_vnf
       ```

 - NS descriptor:
    - First, create the package, and edit the default NS descriptor (the used one in on the directory `ns_k8s_master`). Then, validate and upload the NS package:
       ```bash
       # create the base descriptors
       $ osm package-create --base-directory ns_k8s_master ns ns_k8s_master

       # validate and upload create the package
       $ osm --user netedge --password <password> --project netedge nspkg-create ns_k8s_master/ns_k8s_master_vnf
       ```

### Instantiate the NS with the corresponding VNF

```bash
$ osm --user netedge --password <password> --project netedge ns-create --ns_name ns_k8s_master --nsd_name k8s_master_ns --vim_account NETEDGE_MEC
```
