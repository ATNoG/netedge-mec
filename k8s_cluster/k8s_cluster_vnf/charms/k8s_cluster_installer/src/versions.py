from enum import Enum


class PackageVersions(str, Enum):
    curl = "7.68.0-1ubuntu2.7"
    apt_transport_https = "2.0.6"
    
    git  = "1:2.25.1-1ubuntu3.2"
    wget = "1.20.3-1ubuntu2"
    
    kubelet = "1.22.7-00"
    kubeadm = "1.22.7-00"
    kubectl = "1.22.7-00"
    
    gnupg2 = "2.2.19-3ubuntu2.1"
    software_properties_common = "0.99.9.8"
    ca_certificates = "20210119~20.04.2"

    containerd_io = "1.4.12-1"
