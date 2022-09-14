import os
import time
import shlex
import subprocess
import json
import yaml
import requests
import re

NUMBER_TESTS = 35

USER_MAIN = 'admin'
PASSWORD_MAIN = 'Olaadeus1!'
PROJECT_MAIN = 'admin'
IP_ADDR = '10.0.12.98'
VIM_ACCOUNT_MAIN = 'NetEdge'

DIR_CHARMED_cluster_vnf = 'k8s_cluster/charmed_osm_knf/charmed_cluster_vnf'
DIR_OSM_CLUSTER_VNF = 'k8s_cluster/k8s_osm_cluster_vnf'
DIR_CLUSTER_VNF = 'k8s_cluster/k8s_cluster_vnf'

DIR_OSM_CLUSTER_NS = 'k8s_cluster/k8s_osm_cluster_ns'
DIR_CLUSTER_NS = 'k8s_cluster/k8s_cluster_ns'

PATH_OSM_NS_CONFIG_FILE = 'k8s_cluster/k8s_osm_cluster_ns_params.yaml'
PATH_CLUSTER_NS_CONFIG_FILE = 'k8s_cluster/ns_params.yaml'

PATH_JOIN_PARAMS_FILE = 'k8s_cluster/join_k8s_workers_params.yaml'

CLUSTER_FOR_OSM_NAME = 'edge'
CHARMED_OSM_NAME = 'osm'

USER_CHARMED_OSM = 'admin'
PASSWORD_CHARMED_OSM = 'admin'
PROJECT_CHARMED_OSM = 'admin'
VIM_CHARMED_OSM = 'NetEdge'

DIR_MEC_APP_VNF = '/home/escaleira@av.it.pt/mp1-test-app-mec/docker-img-application/osm/mp1_test_application_vnf'
DIR_MEC_APP_NS = '/home/escaleira@av.it.pt/mp1-test-app-mec/docker-img-application/osm/mp1_test_application_ns'

PATH_MEC_APP_DEPLOYMENT = '/home/escaleira@av.it.pt/mp1-test-app-mec/docker-img-application/osm/mp1_test_application_vnf/helm-chart-v3s/launch_mp1_test/templates/deployment.yaml'

CLUSTER_USERNAME = "controller"
CLUSTER_PASSWORD = "olaadeus"
CHARMED_OSM_NAMESPACE = 'osm-charms-oops'

    
def gather_timestamps_from_kafka(results_path: str):
    # Create container
    output = subprocess.run(shlex.split(
        f"""
        kubectl apply -f ./results/deployment.yaml -n osm
        """
    ))
    print(output)
    
    # Leave time for containers to initialize properly
    time.sleep(60)

    # Create dump dir
    dir1 = subprocess.run(shlex.split(
        f"""
        mkdir /tmp/dump_pod1
        """
    ))
    print(dir1)

    # Obtain pod name
    pod1_name = subprocess.run(shlex.split(
        f"""
        kubectl get pods --no-headers -o custom-columns=':metadata.name' -n osm
        """
    ), stdout=subprocess.PIPE)
    print(pod1_name)

    pod1_name = list(filter(re.compile(r"kafka-dump.*").match, pod1_name.stdout.decode().split("\n")))[0]
    
    # Copy from POD to Local Machine
    copy_pod1 = subprocess.run(shlex.split(
        f"""
        kubectl cp osm/{pod1_name}:/home/kafka/dump/ /tmp/dump_pod1/
        """
    ))
    print(copy_pod1)

    dump_pod1 = subprocess.run(shlex.split(
        f"""
        cp -r /tmp/dump_pod1/ {results_path}
        """
    ))
    print(dump_pod1)

def main():
    # init_environment()
    
    for i in range(1, NUMBER_TESTS+3):

        print("#######################################################################")
        print(f"Test <{i}>")
        print("#######################################################################")
        print(f"Init timestamp: <{time.time()}>")
        print("#######################################################################")

        # create directory for this iteration results
        results_path = f"./results_iteration_{i}/"
        os.mkdir(results_path)
        
        print(f"\n\n\n<{time.time()}> - Scale out\n")
        output = subprocess.run(shlex.split(
            f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password '{PASSWORD_MAIN}' --project {PROJECT_MAIN} 
            vnf-scale edge cluster_vnf --scaling-group worker-scale --scale-out --wait"""
        ))
        print(output)
        
        print(f"\n\n\n<{time.time()}> - Scale in\n")
        output = subprocess.run(shlex.split(
            f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password '{PASSWORD_MAIN}' --project {PROJECT_MAIN} 
            vnf-scale edge cluster_vnf --scaling-group worker-scale --scale-in --wait"""
        ))
        print(output)
        
        gather_timestamps_from_kafka(results_path)
        output = subprocess.run(shlex.split(
            f"""kubectl delete deployment kafka-dump -n osm"""
        ))
        time.sleep(180)
        print(output)
        print(f"\n\n\n<{time.time()}> - Remove tmp directory\n")
        output = subprocess.run(shlex.split(
            f"""rm -rf /tmp/dump_pod1"""
        ))
        print(output)

if __name__ == '__main__':
    main()
    #clean_environment(ns_osm_name=CLUSTER_FOR_OSM_NAME, ns_main_name=CHARMED_OSM_NAME)
