```bash
$ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge nfpkg-create k8s_cluster_vnf
$ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge nspkg-create k8s_cluster_ns
$ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge ns-create --ns_name k8s --nsd_name k8s_cluster_nsd --vim_account NETEDGE_MEC --config_file ns_params.yaml
```

 - Take into consideration the name of the NS (TODO)


## Execute a primitive for some VDU, if there are multiple instances
TODO

```bash
$ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge ns-action k8s --vnf_name 1 --vdu_id controller --action_name get-k8s-controller-info --wait
```

```bash
$ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge ns-action k8s --vnf_name 1 --vdu_id worker --vdu_count 1 --action_name join-k8s-workers --params_file join_k8s_workers_params.yaml --wait
```
