```bash
$ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge nfpkg-create k8s_cluster_vnf
$ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge nspkg-create k8s_cluster_ns
$ osm --hostname 10.0.12.96 --user netedge --password <password> --project netedge ns-create --ns_name k8s_cluster_ns --nsd_name k8s_cluster_nsd --vim_account NETEDGE_MEC
```