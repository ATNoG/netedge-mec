import os
import time
import shlex
import subprocess
import json
import yaml
import requests
import re

NUMBER_TESTS = 8

USER_MAIN = 'netedge'
PASSWORD_MAIN = ''
PROJECT_MAIN = 'netedge'
IP_ADDR = '10.0.12.98'
VIM_ACCOUNT_MAIN = 'NetEdge'

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

USER_CHARMED_OSM = 'admin'
PASSWORD_CHARMED_OSM = 'admin'
PROJECT_CHARMED_OSM = 'admin'
VIM_CHARMED_OSM = 'NetEdge'

DIR_MEC_APP_VNF = '/home/escaleira@av.it.pt/mp1-test-app-mec/docker-img-application/osm/mp1_test_application_vnf'
DIR_MEC_APP_NS = '/home/escaleira@av.it.pt/mp1-test-app-mec/docker-img-application/osm/mp1_test_application_ns'

PATH_MEC_APP_DEPLOYMENT = '/home/escaleira@av.it.pt/mp1-test-app-mec/docker-img-application/osm/mp1_test_application_vnf/helm-chart-v3s/launch_mp1_test/templates/deployment.yaml'

CLUSTER_USERNAME = "controller"
CLUSTER_PASSWORD = "olaadeus"
CHARMED_OSM_NAMESPACE = 'osm-charm-oops'


def init_environment():
    # create VNF packages
    for dir_name in (DIR_CHARMED_OSM_VNF, DIR_OSM_CLUSTER_VNF, DIR_CLUSTER_VNF):
        print(f"\n\n\n<{time.time()}> - Creating VNF package for {dir_name}\n")
        output = subprocess.run(shlex.split(
            f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} nfpkg-create {dir_name}"""
        ))
        print(output)

    # create NS packages
    for dir_name in (DIR_OSM_CLUSTER_NS, DIR_CLUSTER_NS):
        print(f"\n\n\n<{time.time()}> - Creating NS package for {dir_name}\n")
        output = subprocess.run(shlex.split(
            f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} nspkg-create {dir_name}"""
        ))
        print(output)
    

def instantiate_ns(ns_name, vnf_name_master, nsd_name, ns_config_file, results_path: str):
    # instantiate cluster
    print(f"\n\n\n<{time.time()}> - Instantiate cluster {ns_name}\n")
    output = subprocess.run(shlex.split(
        f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} ns-create 
        --ns_name {ns_name} --nsd_name {nsd_name} --vim_account {VIM_ACCOUNT_MAIN} --config_file {ns_config_file} --wait"""
    ))
    print(output)

    # join worker to master
    print(f"\n\n\n<{time.time()}> - Obtain the master information\n")
    output = subprocess.run(shlex.split(
        f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} ns-action {ns_name} 
        --vnf_name {vnf_name_master} --vdu_id controller --action_name get-k8s-controller-info --wait"""
    ), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(output)

    err = output.stderr.decode('utf-8')
    d = err[err.find('{'): err.rfind('}') + 1]
    d = d.replace("{'", '{"').replace("', '", '", "').replace("': '", '": "').replace("': ", '": ').replace(", '", ', "').replace("'}", '"}')

    ca_cert_hash = json.loads(d).get('ca-cert-hash')
    controller_ip = json.loads(d).get('controller-ip')
    join_token = json.loads(d).get('join-token')

    with open(PATH_JOIN_PARAMS_FILE, 'r') as file:
        data_yaml = yaml.safe_load(file)

    data_yaml['cert'] = ca_cert_hash
    data_yaml['ip'] = controller_ip
    data_yaml['token'] = join_token

    with open(PATH_JOIN_PARAMS_FILE, 'w') as file:
        yaml.safe_dump(data_yaml, file)

    print(f"\n\n\n<{time.time()}> - Join worker to master\n")
    output = subprocess.run(shlex.split(
        f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} ns-action {ns_name} 
        --vnf_name {vnf_name_master} --vdu_id worker --vdu_count 0 --action_name join-k8s-workers --params_file {PATH_JOIN_PARAMS_FILE} --wait"""
    ), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(output)
        
        
def instantiate_mec_app(charmed_osm_master_ip: str):
    # instantiate MEC APP
    print(f"\n\n\n<{time.time()}> - Create VNF package for the MEC APP\n")
    output = subprocess.run(shlex.split(
        f"""osm --hostname {charmed_osm_master_ip} --user {USER_CHARMED_OSM} --password '{PASSWORD_CHARMED_OSM}' --project {PROJECT_CHARMED_OSM} 
        nfpkg-create {DIR_MEC_APP_VNF}"""
    ))
    print(output)

    print(f"\n\n\n<{time.time()}> - Create NS package for the MEC APP\n")
    output = subprocess.run(shlex.split(
        f"""osm --hostname {charmed_osm_master_ip} --user {USER_CHARMED_OSM} --password '{PASSWORD_CHARMED_OSM}' --project {PROJECT_CHARMED_OSM} 
        nspkg-create {DIR_MEC_APP_NS}"""
    ))
    print(output)

    print(f"\n\n\n<{time.time()}> - Instantiate MEC APP\n")
    output = subprocess.run(shlex.split(
        f"""osm --hostname {charmed_osm_master_ip} --user {USER_CHARMED_OSM} --password '{PASSWORD_CHARMED_OSM}' --project {PROJECT_CHARMED_OSM} ns-create 
        --ns_name mp1 --nsd_name mp1_test_application_ns --vim_account {VIM_CHARMED_OSM} --wait"""
    ))
    print(output)
    
def gather_timestamps_from_kafka(results_path: str, charmed_osm_master_ip: str):
    # Send file to the other Cluster
    output = subprocess.run(shlex.split(
        f"""
        sshpass -p {CLUSTER_PASSWORD} scp -o StrictHostKeyChecking=no -q ./results/deployment.yaml {CLUSTER_USERNAME}@{charmed_osm_master_ip}:~/
        """
    ))
    print(output)
    
    output = subprocess.run(shlex.split(
        f"""
        sshpass -p {CLUSTER_PASSWORD} ssh -o StrictHostKeyChecking=no -q {CLUSTER_USERNAME}@{charmed_osm_master_ip} kubectl apply -f ~/deployment.yaml -n {CHARMED_OSM_NAMESPACE}
        """
    ))
    print(output)
    
    # Leave time for containers to initialize properly
    time.sleep(60*3)

    dir2 = subprocess.run(shlex.split(
        f"""
        sshpass -p {CLUSTER_PASSWORD} ssh -o StrictHostKeyChecking=no -q {CLUSTER_USERNAME}@{charmed_osm_master_ip} mkdir /tmp/dump_pod2
        """
    ))
    print(dir2)
    
    pod2_name = subprocess.run(shlex.split(
        f"""
        sshpass -p {CLUSTER_PASSWORD} ssh -o StrictHostKeyChecking=no -q {CLUSTER_USERNAME}@{charmed_osm_master_ip} kubectl get pods --no-headers -o  custom-columns='"':metadata.name'"' -n {CHARMED_OSM_NAMESPACE}
        """
    ), stdout=subprocess.PIPE)
    print(pod2_name)
    
    pod2_name = list(filter(re.compile(r"kafka-dump.*").match, pod2_name.stdout.decode().split("\n")))[0]
 
    copy_pod2 = subprocess.run(shlex.split(
        f"""
        sshpass -p {CLUSTER_PASSWORD} ssh -o StrictHostKeyChecking=no -q {CLUSTER_USERNAME}@{charmed_osm_master_ip} kubectl cp {CHARMED_OSM_NAMESPACE}/{pod2_name}:/home/kafka/dump/ /tmp/dump_pod2/
        """
    ))
    print(copy_pod2)
    
    dump_pod2 = subprocess.run(shlex.split(
        f"""
        sshpass -p {CLUSTER_PASSWORD} scp -o StrictHostKeyChecking=no -r -q {CLUSTER_USERNAME}@{charmed_osm_master_ip}:/tmp/dump_pod2/ {results_path}
        """
    ))
    print(dump_pod2)
    

def clean_environment(charmed_osm_master_ip: str):

    print(f"\n\n\n<{time.time()}> - Delete mp1\n")
    output = subprocess.run(shlex.split(
        f"""osm --hostname {charmed_osm_master_ip} --user {USER_CHARMED_OSM} --password '{PASSWORD_CHARMED_OSM}' --project {PROJECT_CHARMED_OSM} ns-delete 
        mp1 --wait"""
    ), timeout=5*60)
    print(output)

    time.sleep(60*2)


def main():
    # init_environment()
    
    for i in range(0, NUMBER_TESTS+3):

        print("#######################################################################")
        print(f"Test <{i}>")
        print("#######################################################################")
        print(f"Init timestamp: <{time.time()}>")
        print("#######################################################################")

        output = subprocess.run(shlex.split(
            f"""juju models --all"""
        ), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(output)

        global CHARMED_OSM_NAMESPACE
        if CHARMED_OSM_NAMESPACE in output.stdout.decode('utf-8'):
            with open(PATH_CLUSTER_NS_CONFIG_FILE, 'r') as file:
                data_yaml = yaml.safe_load(file)

            data_yaml['additionalParamsForVnf'][1]['additionalParamsForKdu'][0]['k8s-namespace'] = data_yaml['additionalParamsForVnf'][1]['additionalParamsForKdu'][0]['k8s-namespace'] + '-oops'
            data_yaml['additionalParamsForVnf'][1]['additionalParamsForKdu'][1]['k8s-namespace'] = data_yaml['additionalParamsForVnf'][1]['additionalParamsForKdu'][1]['k8s-namespace'] + '-oops'
            CHARMED_OSM_NAMESPACE = data_yaml['additionalParamsForVnf'][1]['additionalParamsForKdu'][1]['k8s-namespace']
    
            with open(PATH_CLUSTER_NS_CONFIG_FILE, 'w') as file:
                yaml.safe_dump(data_yaml, file)
        
        # create directory for this iteration results
        results_path = f"./results_iteration_{i}/"
        os.mkdir(results_path)

        # obtain the IP addr of the first NS master
        print(f"\n\n\n<{time.time()}> - Obtaining master's IP addr\n")
        output = subprocess.run(shlex.split(
            f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} vnf-list --ns {CLUSTER_FOR_OSM_NAME}"""
        ), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(output)

        time.sleep(60)

        all_output = output.stdout.decode('utf-8')
        ip_addr_start_index = all_output.find('10.0.')
        ip_addr_end_index = all_output.find(' ', ip_addr_start_index)
        charmed_osm_master_ip = all_output[ip_addr_start_index:ip_addr_end_index]

        print(f"Charmed OSM master's IP: {charmed_osm_master_ip}")
        
        with open(PATH_MEC_APP_DEPLOYMENT, 'r') as file:
            data_yaml = yaml.safe_load(file)

        data_yaml['spec']['template']['spec']['containers'][0]['env'][0]['value'] = f"http://{charmed_osm_master_ip}:30080"
        
        with open(PATH_MEC_APP_DEPLOYMENT, 'w') as file:
            yaml.safe_dump(data_yaml, file)

        instantiate_mec_app(charmed_osm_master_ip=charmed_osm_master_ip)

        print(f"\n\n\n<{time.time()}> - Finished deployment\n")
#
        gather_timestamps_from_kafka(results_path, charmed_osm_master_ip=charmed_osm_master_ip)
#
        clean_environment(charmed_osm_master_ip=charmed_osm_master_ip)
        
        print("#######################################################################")
        print(f"Test <{i}> finished at <{time.time()}>")
        print("#######################################################################\n\n\n")

if __name__ == '__main__':
    main()
    #clean_environment(ns_osm_name=CLUSTER_FOR_OSM_NAME, ns_main_name=CHARMED_OSM_NAME)
