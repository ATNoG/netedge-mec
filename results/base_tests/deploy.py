import os
import time
import shlex
import subprocess
import re

NUMBER_TESTS = 20

USER_MAIN = 'netedge'
PASSWORD_MAIN = ''
PROJECT_MAIN = 'netedge'
IP_ADDR = '10.0.12.98'
VIM_ACCOUNT_MAIN = 'NetEdge'


def init_environment():
    # create VNF packages
    dir_name = 'base_vnf'
    print(f"\n\n\n<{time.time()}> - Creating VNF package for {dir_name}\n")
    output = subprocess.run(shlex.split(
        f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password '{PASSWORD_MAIN}' --project {PROJECT_MAIN} nfpkg-create {dir_name}"""
    ))
    print(output)
    
    dir_name = 'base_ns'
    print(f"\n\n\n<{time.time()}> - Creating VNF package for {dir_name}\n")
    output = subprocess.run(shlex.split(
        f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password '{PASSWORD_MAIN}' --project {PROJECT_MAIN} nspkg-create {dir_name}"""
    ))
    print(output)


def instantiate_ns(ns_name, vnf_name_master, nsd_name, results_path: str):
    # instantiate cluster
    print(f"\n\n\n<{time.time()}> - Instantiate cluster {ns_name}\n")
    output = subprocess.run(shlex.split(
        f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password '{PASSWORD_MAIN}' --project {PROJECT_MAIN} ns-create 
        --ns_name {ns_name} --nsd_name {nsd_name} --vim_account {VIM_ACCOUNT_MAIN} --wait"""
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
    
    # SCP to our machine
    dump_pod1 = subprocess.run(shlex.split(
        f"""
        cp -r /tmp/dump_pod1/ {results_path}
        """
    ))
    print(dump_pod1)


def clean_environment(ns_name: str):
    # just to be sure, run two times in a row
    try:
        for i in range(2):
            print(f"\n\n\n<{time.time()}> - Delete NS {ns_name} - {i}\n")
            output = subprocess.run(shlex.split(
                f"""osm --hostname {IP_ADDR} --user {USER_MAIN} --password '{PASSWORD_MAIN}' --project {PROJECT_MAIN} ns-delete 
                {ns_name} --wait"""
            ), timeout=5*60)
            print(output)
    except Exception as e:
        print(e)
        
    # and just to be really sure
    # print(f"\n\n\n<{time.time()}> - Delete all OSM resources\n")
    # output = subprocess.run(shlex.split(
    #     f"""sh ../delete_all_osm_resources.sh"""
    # ))
    # print(output)
    
    print(f"\n\n\n<{time.time()}> - Delete our results container\n")
    output = subprocess.run(shlex.split(
        f"""kubectl scale deployment kafka-dump -n osm --replicas=0"""
    ))
    output = subprocess.run(shlex.split(
        f"""kubectl delete deployment kafka-dump -n osm"""
    ))
    print(output)
    
    # print(f"\n\n\n<{time.time()}> - Destroy and init LCM\n")
    # output = subprocess.run(shlex.split(
    #     f"""kubectl scale deployment lcm -n osm --replicas=0"""
    # ))
    # output = subprocess.run(shlex.split(
    #     f"""kubectl scale deployment lcm -n osm --replicas=1"""
    # ))
    # print(output)

    print(f"\n\n\n<{time.time()}> - Remove tmp directory\n")
    output = subprocess.run(shlex.split(
        f"""rm -rf /tmp/dump_pod1"""
    ))
    print(output)

    time.sleep(60*2)


def main():
    init_environment()
    
    for i in range(0, NUMBER_TESTS+3):
        print("#######################################################################")
        print(f"Test <{i}>")
        print("#######################################################################")
        print(f"Init timestamp: <{time.time()}>")
        print("#######################################################################")
        
        # create directory for this iteration results
        results_path = f"./results_iteration_{i}/"
        os.mkdir(results_path)
        
        # instantiate cluster for OSM
        instantiate_ns(ns_name='base_ns', vnf_name_master='base_vnf', nsd_name='base_nsd', results_path=results_path)

        time.sleep(60)

        gather_timestamps_from_kafka(results_path)

        # Start cleaning for the next iteration
        clean_environment(ns_name='base_ns')
        
        print("#######################################################################")
        print(f"Test <{i}> finished at <{time.time()}>")
        print("#######################################################################\n\n\n")

if __name__ == '__main__':
    main()
