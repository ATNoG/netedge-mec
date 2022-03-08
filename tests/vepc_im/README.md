 - From the documentation page [VNF Onboarding Walkthrough](https://osm.etsi.org/docs/vnf-onboarding-guidelines/06-walkthrough.html?highlight=vca).

 - This example was created with pre-SOL006 (SOL005), for an OSM version previous to the 9 one. Therefore, it is necessary to obtain the VNFD and NSD for the new version of OSM:
     ```bash
     $ osm descriptor-translate vepc_vnfd.yaml > vepc_vnfd_new.yaml             # for the VNFD
     $ osm descriptor-translate vepc_nsd.yaml > vepc_nsd_new.yaml               # for the NSD
     ```