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
CHARMED_OSM_NAMESPACE = 'osm-charms-oops'


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
    
    # Create container
    output = subprocess.run(shlex.split(
        f"""
        kubectl apply -f ./results/deployment.yaml -n osm
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

    # Create dump dir
    dir1 = subprocess.run(shlex.split(
        f"""
        mkdir /tmp/dump_pod1
        """
    ))
    print(dir1)
    
    dir2 = subprocess.run(shlex.split(
        f"""
        sshpass -p {CLUSTER_PASSWORD} ssh -o StrictHostKeyChecking=no -q {CLUSTER_USERNAME}@{charmed_osm_master_ip} mkdir /tmp/dump_pod2
        """
    ))
    print(dir2)
    
    # Obtain pod name
    pod1_name = subprocess.run(shlex.split(
        f"""
        kubectl get pods --no-headers -o custom-columns=':metadata.name' -n osm
        """
    ), stdout=subprocess.PIPE)
    print(pod1_name)

    pod1_name = list(filter(re.compile(r"kafka-dump.*").match, pod1_name.stdout.decode().split("\n")))[0]
    
    pod2_name = subprocess.run(shlex.split(
        f"""
        sshpass -p {CLUSTER_PASSWORD} ssh -o StrictHostKeyChecking=no -q {CLUSTER_USERNAME}@{charmed_osm_master_ip} kubectl get pods --no-headers -o  custom-columns='"':metadata.name'"' -n {CHARMED_OSM_NAMESPACE}
        """
    ), stdout=subprocess.PIPE)
    print(pod2_name)
    
    pod2_name = list(filter(re.compile(r"kafka-dump.*").match, pod2_name.stdout.decode().split("\n")))[0]
    
    # Copy from POD to Local Machine
    copy_pod1 = subprocess.run(shlex.split(
        f"""
        kubectl cp osm/{pod1_name}:/home/kafka/dump/ /tmp/dump_pod1/
        """
    ))
    print(copy_pod1)
    
    copy_pod2 = subprocess.run(shlex.split(
        f"""
        sshpass -p {CLUSTER_PASSWORD} ssh -o StrictHostKeyChecking=no -q {CLUSTER_USERNAME}@{charmed_osm_master_ip} kubectl cp {CHARMED_OSM_NAMESPACE}/{pod2_name}:/home/kafka/dump/ /tmp/dump_pod2/
        """
    ))
    print(copy_pod2)
    
    # SCP to our machine
    dump_pod1 = subprocess.run(shlex.split(
        f"""
        cp -r /tmp/dump_pod1/ {results_path}
        """
    ))
    print(dump_pod1)
    
    dump_pod2 = subprocess.run(shlex.split(
        f"""
        sshpass -p {CLUSTER_PASSWORD} scp -o StrictHostKeyChecking=no -r -q {CLUSTER_USERNAME}@{charmed_osm_master_ip}:/tmp/dump_pod2/ {results_path}
        """
    ))
    print(dump_pod2)

def clean_environment(ns_osm_name: str, ns_main_name: str):
    # just to be sure, run two times in a row
    try:
        for i in range(2):
            print(f"\n\n\n<{time.time()}> - Delete OSM NS {ns_osm_name} - {i}\n")
            output = subprocess.run(shlex.split(
                f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} ns-delete 
                {ns_osm_name} --wait"""
            ), timeout=5*60)
            print(output)

            print(f"\n\n\n<{time.time()}> - Delete OSM cluster - {i}\n")
            output = subprocess.run(shlex.split(
                f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} k8scluster-delete 
                k8s_test --force --wait"""
            ))
            print(output)

            #print(f"\n\n\n<{time.time()}> - Delete OSM NS {ns_main_name} - {i}\n")
            #output = subprocess.run(shlex.split(
            #    f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} ns-delete 
            #    {ns_main_name} --wait"""
            #), timeout=5*60)
            #print(output)

    except Exception as e:
        print(e)
        
        # edit the NS config file for the second cluster
        with open(PATH_CLUSTER_NS_CONFIG_FILE, 'r') as file:
            data_yaml = yaml.safe_load(file)

        data_yaml['additionalParamsForVnf'][1]['additionalParamsForKdu'][0]['k8s-namespace'] = data_yaml['additionalParamsForVnf'][1]['additionalParamsForKdu'][0]['k8s-namespace'] + '-oops'
        data_yaml['additionalParamsForVnf'][1]['additionalParamsForKdu'][1]['k8s-namespace'] = data_yaml['additionalParamsForVnf'][1]['additionalParamsForKdu'][1]['k8s-namespace'] + '-oops'
        CHARMED_OSM_NAMESPACE = data_yaml['additionalParamsForVnf'][1]['additionalParamsForKdu'][1]['k8s-namespace']

        with open(PATH_CLUSTER_NS_CONFIG_FILE, 'w') as file:
            yaml.safe_dump(data_yaml, file)
        
    # and just to be really sure
    print(f"\n\n\n<{time.time()}> - Delete all OSM resources\n")
    output = subprocess.run(shlex.split(
        f"""sh results/delete_all_osm_resources.sh"""
    ))
    print(output)
    
    print(f"\n\n\n<{time.time()}> - Delete our results container\n")
    output = subprocess.run(shlex.split(
        f"""kubectl scale deployment kafka-dump -n osm --replicas=0"""
    ))
    output = subprocess.run(shlex.split(
        f"""kubectl delete deployment kafka-dump -n osm"""
    ))
    print(output)
    
    print(f"\n\n\n<{time.time()}> - Destroy and init LCM\n")
    output = subprocess.run(shlex.split(
        f"""kubectl scale deployment lcm -n osm --replicas=0"""
    ))
    output = subprocess.run(shlex.split(
        f"""kubectl scale deployment lcm -n osm --replicas=1"""
    ))
    print(output)

    print(f"\n\n\n<{time.time()}> - Remove tmp directory\n")
    output = subprocess.run(shlex.split(
        f"""rm -rf /tmp/dump_pod1"""
    ))
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
        
        # instantiate cluster for OSM
        instantiate_ns(ns_name=CLUSTER_FOR_OSM_NAME, vnf_name_master='osm_vnf', nsd_name='k8s_osm_cluster_nsd', ns_config_file=PATH_OSM_NS_CONFIG_FILE, results_path=results_path)
        
#        # Execute primitive to download all the necessary charmed OSM images
#        print(f"\n\n\n<{time.time()}> - Execute primitive to download all the necessary charmed OSM images\n")
#        for vdu in ('controller', 'worker'):
#            output = subprocess.run(shlex.split(
#                f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} ns-action {CLUSTER_FOR_OSM_NAME} 
#                --vnf_name osm_vnf --vdu_id {vdu} --action_name download-charmed-osm-images --wait"""
#            ), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#            print(output)
#
#        # obtain the IP addr of the first NS master
#        print(f"\n\n\n<{time.time()}> - Obtaining master's IP addr\n")
#        output = subprocess.run(shlex.split(
#            f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} vnf-list --ns {CLUSTER_FOR_OSM_NAME}"""
#        ), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#        print(output)
#
#        time.sleep(60)
#
#        all_output = output.stdout.decode('utf-8')
#        ip_addr_start_index = all_output.find('10.0.')
#        ip_addr_end_index = all_output.find(' ', ip_addr_start_index)
#        charmed_osm_master_ip = all_output[ip_addr_start_index:ip_addr_end_index]
#
#        print(f"Charmed OSM master's IP: {charmed_osm_master_ip}")
#
#        # edit the NS config file for the second cluster
#        with open(PATH_CLUSTER_NS_CONFIG_FILE, 'r') as file:
#            data_yaml = yaml.safe_load(file)
#
#        data_yaml['additionalParamsForVnf'][0]['additionalParams']['osm_url'] = f"https://{charmed_osm_master_ip}:9999"
#
#        with open(PATH_CLUSTER_NS_CONFIG_FILE, 'w') as file:
#            yaml.safe_dump(data_yaml, file)
#
#        # instantiate Charmed OSM
#        instantiate_ns(ns_name=CHARMED_OSM_NAME, vnf_name_master='cluster_vnf', nsd_name='k8s_cluster_nsd', ns_config_file=PATH_CLUSTER_NS_CONFIG_FILE, results_path=results_path)
#
#        time.sleep(60)
#        
#        with open(PATH_MEC_APP_DEPLOYMENT, 'r') as file:
#            data_yaml = yaml.safe_load(file)
#        
#        data_yaml['spec']['template']['spec']['containers'][0]['env'][0]['value'] = f"http://{charmed_osm_master_ip}:30080"
#        
#        with open(PATH_MEC_APP_DEPLOYMENT, 'w') as file:
#            yaml.safe_dump(data_yaml, file)
#
#        instantiate_mec_app(charmed_osm_master_ip=charmed_osm_master_ip)
#
#        print(f"\n\n\n<{time.time()}> - Finished deployment\n")
#
#        gather_timestamps_from_kafka(results_path, charmed_osm_master_ip=charmed_osm_master_ip)
#
        # obtain the NS instantiation details (first, warm up, because NBI does some kind of weird cache)
        # First, login with OSM using the credentials given by param
        osm_url = f"https://{IP_ADDR}:9999"
        response = requests.post(f"{osm_url}/osm/admin/v1/tokens", json={
            "username": USER_MAIN,
            "password": PASSWORD_MAIN
        }, headers={
            "Accept": "application/json"
        }, verify=False)

        print(response.status_code)

        token = response.json()['id']
        trials = 0
        while True:
            subprocess.run(shlex.split(
               f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} ns-list"""
            ))
            subprocess.run(shlex.split(
               f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} vnf-list"""
            ))
            subprocess.run(shlex.split(
               f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} vim-list"""
            ))
            subprocess.run(shlex.split(
               f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} k8s-list"""
            ))
            subprocess.run(shlex.split(
               f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} vnfd-list"""
            ))
            subprocess.run(shlex.split(
               f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} vca-list"""
            ))
            subprocess.run(shlex.split(
               f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} user-list"""
            ))
            subprocess.run(shlex.split(
               f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} project-list"""
            ))

            response = requests.get(f"{osm_url}/osm/nslcm/v1/ns_instances", headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }, verify=False)

            if response.status_code != 200:
                error_info = f"Response with status code: <{response.status_code}>; Response: <{response.json()}>"
                print(error_info)
    
            nsi_ids = []
            for ns_instance in response.json():
                print(ns_instance)
                if CLUSTER_FOR_OSM_NAME == ns_instance['name']:
                    nsi_ids.append(ns_instance['_id'])

            print(f"NSIs: {nsi_ids}")
    
            for i in nsi_ids:
                response = requests.get(f"{osm_url}/osm/nslcm/v1/ns_instances/{i}?vcaStatusRefresh=true", headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                }, verify=False)
                print(f"{response.status_code} -> {response.json()}\n\n\n")

            time.sleep(60)

            stop = {CLUSTER_FOR_OSM_NAME: '', CHARMED_OSM_NAME: ''}
            for ns_name in (CLUSTER_FOR_OSM_NAME):      # , CHARMED_OSM_NAME
                print(f"\n\n\n<{time.time()}> - Obtain the NS instantiation details\n")
                subprocess.run(shlex.split(
                    f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} ns-show 
                    {ns_name} --literal"""
                ))
                time.sleep(20)
                output = subprocess.run(shlex.split(
                    f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password {PASSWORD_MAIN} --project {PROJECT_MAIN} ns-show 
                    {ns_name} --literal"""
                ), stdout=subprocess.PIPE)

                with open(f"{results_path}{ns_name}.yaml", 'w') as file:
                    file.write(output.stdout.decode('utf-8'))
            if stop[CLUSTER_FOR_OSM_NAME]:
                break
            
            if trials > 1:
                break

            nsi_ids = []
            for ns_instance in response.json():
                print(ns_instance)
                if stop[CHARMED_OSM_NAME] and CHARMED_OSM_NAME == ns_instance['name']:
                    nsi_ids.append(ns_instance['_id'])

            print(f"NSIs: {nsi_ids}")
    
            for i in nsi_ids:
                response = requests.get(f"{osm_url}/osm/nslcm/v1/ns_instances/{i}?vcaStatusRefresh=true", headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                }, verify=False)
                print(f"{response.status_code} -> {response.json()}\n\n\n")

            trials += 1

        # Start cleaning for the next iteration
        clean_environment(ns_osm_name=CHARMED_OSM_NAME, ns_main_name=CLUSTER_FOR_OSM_NAME)
        
        print("#######################################################################")
        print(f"Test <{i}> finished at <{time.time()}>")
        print("#######################################################################\n\n\n")

if __name__ == '__main__':
    main()
    #clean_environment(ns_osm_name=CLUSTER_FOR_OSM_NAME, ns_main_name=CHARMED_OSM_NAME)
