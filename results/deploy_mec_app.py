import os
import time
import shlex
import subprocess
import json
import yaml
import requests
import re

NUMBER_TESTS = 32

USER_MAIN = 'netedge'
PASSWORD_MAIN = 'Olaadeus1!'
PROJECT_MAIN = 'netedge'
IP_ADDR = '10.0.12.98'
VIM_ACCOUNT_MAIN = 'NetEdgeDummy'

DIR_CHARMED_OSM_VNF = 'k8s_cluster/charmed_osm_knf/charmed_osm_vnf'
DIR_OSM_CLUSTER_VNF = 'k8s_cluster/k8s_osm_cluster_vnf'
DIR_CLUSTER_VNF = 'k8s_cluster/k8s_cluster_vnf'

DIR_OSM_CLUSTER_NS = 'k8s_cluster/k8s_osm_cluster_ns'
DIR_CLUSTER_NS = 'k8s_cluster/k8s_cluster_ns'

PATH_OSM_NS_CONFIG_FILE = 'k8s_cluster/k8s_osm_cluster_ns_params.yaml'
PATH_CLUSTER_NS_CONFIG_FILE = 'k8s_cluster/ns_params.yaml'

PATH_JOIN_PARAMS_FILE = 'k8s_cluster/join_k8s_workers_params.yaml'

CLUSTER_FOR_OSM_NAME = 'osm-cluster'
CHARMED_OSM_NAME = 'osm'

DIR_MEC_APP_VNF = '/home/escaleira@av.it.pt/mp1-test-app-mec/osm/mp1_test_application_vnf'
DIR_MEC_APP_NS = '/home/escaleira@av.it.pt/mp1-test-app-mec/osm/mp1_test_application_ns'

PATH_MEC_APP_DEPLOYMENT = '/home/escaleira@av.it.pt/mp1-test-app-mec/osm/mp1_test_application_vnf/helm-chart-v3s/launch_mp1_test/templates/deployment.yaml'

CLUSTER_USERNAME = "controller"
CLUSTER_PASSWORD = "olaadeus"
CHARMED_OSM_NAMESPACE = 'osm-charm-oops'

MASTER_CLUSTER_IP = " 10.0.13.243"


def instantiate_mec_app():
    # instantiate MEC APP
    print(f"\n\n\n<{time.time()}> - Create VNF package for the MEC APP\n")
    output = subprocess.run(shlex.split(
        f"""osm --user {USER_MAIN} --password '{PASSWORD_MAIN}' --project {PROJECT_MAIN} 
        nfpkg-create {DIR_MEC_APP_VNF}"""
    ))
    print(output)

    print(f"\n\n\n<{time.time()}> - Create NS package for the MEC APP\n")
    output = subprocess.run(shlex.split(
        f"""osm --user {USER_MAIN} --password '{PASSWORD_MAIN}' --project {PROJECT_MAIN} 
        nspkg-create {DIR_MEC_APP_NS}"""
    ))
    print(output)

    print(f"\n\n\n<{time.time()}> - Instantiate MEC APP\n")
    output = subprocess.run(shlex.split(
        f"""osm --user {USER_MAIN} --password '{PASSWORD_MAIN}' --project {PROJECT_MAIN} ns-create 
        --ns_name mp1 --nsd_name mp1_test_application_ns --vim_account {VIM_ACCOUNT_MAIN} --wait"""
    ))
    print(output)
    
def gather_timestamps_from_kafka(results_path: str):
    # Create container
    output = subprocess.run(shlex.split(
        f"""
        kubectl apply -f ./results/deployment.yaml -n osm
        """
    ))
    print(output)
    
    # Leave time for containers to initialize properly
    time.sleep(60*3)

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

    output = subprocess.run(shlex.split(
        f"""kubectl delete deployment kafka-dump -n osm"""
    ))
    print(output)

def clean_environment():

    print(f"\n\n\n<{time.time()}> - Delete mp1\n")
    output = subprocess.run(shlex.split(
        f"""osm --user {USER_MAIN} --password '{PASSWORD_MAIN}' --project {PROJECT_MAIN} ns-delete 
        mp1 --wait"""
    ), timeout=5*60)
    print(output)

    subprocess.run(shlex.split(
        f"""
        rm -rf /tmp/dump_pod1/
        """
    ))

    time.sleep(30)


def main():
    # init_environment()
    
    for i in range(25, NUMBER_TESTS):

        print("#######################################################################")
        print(f"Test <{i}>")
        print("#######################################################################")
        print(f"Init timestamp: <{time.time()}>")
        print("#######################################################################")

        # create directory for this iteration results
        results_path = f"./results_iteration_{i}/"
        os.mkdir(results_path)

        charmed_osm_master_ip = MASTER_CLUSTER_IP

        print(f"Charmed OSM master's IP: {charmed_osm_master_ip}")
        
        with open(PATH_MEC_APP_DEPLOYMENT, 'r') as file:
            data_yaml = yaml.safe_load(file)

        data_yaml['spec']['template']['spec']['containers'][0]['env'][0]['value'] = f"http://{charmed_osm_master_ip}:30080"
        
        with open(PATH_MEC_APP_DEPLOYMENT, 'w') as file:
            yaml.safe_dump(data_yaml, file)

        instantiate_mec_app()

        print(f"\n\n\n<{time.time()}> - Finished deployment\n")

        gather_timestamps_from_kafka(results_path)

        clean_environment()
        
        print("#######################################################################")
        print(f"Test <{i}> finished at <{time.time()}>")
        print("#######################################################################\n\n\n")

if __name__ == '__main__':
    main()
    #clean_environment()
