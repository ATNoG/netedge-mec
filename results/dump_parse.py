import os
import re
import csv
import yaml
import time
from dateutil import parser

def read_ns(dir,count):
    # dump is in a weird state where each data isn't a line 
    # we can used the 'Received Message' to parse lines
    data = []
    tmp_data = None
    with open(dir,"r") as file:
        tmp_data = "\n".join(file.readlines()).split("Received message")
    # remove index 0 which is ''
    tmp_data.pop(0)
    ns_data = ["iteration","instance_start","instance_started","delta"]
    ns_values = [count]
    for data in tmp_data:
        if not re.match("^ dummy message.*",data):
            # get the key value 
            # file should follow order of ns_data otherwise something went wrong :(
            # obtain key value since it is dumped as "key b'<data>'"
            search = re.search("key b'instantiate.?'",data)
            if search:
                # append timestamp
                if search.group()=="key b'instantiate'":
                    ns_values.append(int(data.split(" ")[-1])/1000)
                elif search.group() == "key b'instantiated'":
                    instantiate_start_time = ns_values[-1]
                    instantiated_time = int(data.split(" ")[-1])/1000
                    ns_values.append(instantiated_time)
                    # delta time
                    ns_values.append(instantiated_time-instantiate_start_time)
    
    # loop indexes for csv write and zip
    ns_fields = [ns_data[0]]+[(ns_data[1:] * len(ns_values))][0][:len(ns_values)-1]
    # update the name
    ns_fields = update_name(ns_fields)
    ret = dict(zip(ns_fields,ns_values))
    ret["fields"] = ns_fields
    return ret

def update_name(data):
    # transforms the data to 
    counts = {}
    for index_name in range(len(data)):
        for index_same_name in range(1,len(data)):
            if data[index_name]==data[index_same_name]:
                if data[index_name] in counts:
                    counts[data[index_name]]+=1
                else:
                    counts[data[index_name]]=0
                data[index_same_name] = data[index_same_name]+str(counts[data[index_same_name]])
    return data
            
def read_mep(dir,count):
    # TODO MISSING INITIALIZED TIME FROM NS
    # Order of each mep received action
    mep_data = ["iteration","mep_initializaton","mec_app_ready","mec_app_service_creation","mec_app_subscriptions","mec_app_service_query"]
    mep_values = [count]
    with open(dir,"r") as file:
        line = file.readline()
        while line:
            # Parse the data
            # timestamp is always the latest value and the data contains the order specified in the list above
            # timestamp is in ms transform to s
            mep_values.append(int(line.split(" ")[-1])/1000)
            line = file.readline()
    # return a dict for CSV write for usage in graphical analysis 
    ret = dict(zip(mep_data,mep_values))
    ret["fields"] = mep_data 
    return ret

def pod_dump(dir,main_ns_data,charmed_ns_data,mep_data,count):
    # iterate all known pod dirs and their files
    # Main OSM pod
    main_ns_data.append(read_ns(f"{dir}/dump_pod1/ns",count))
    # Charmed OSM pod
    #charmed_ns_data.append(read_ns(f"{dir}/dump_pod2/ns",count))
    #mep_data.append(read_mep(f"{dir}/dump_pod2/mep",count))
        
def osm_yaml(dir,osm_data,count):
    osm_full_yaml = None
    with open(f"{dir}/osm.yaml","r") as file:
        osm_full_yaml = yaml.load(file,Loader=yaml.FullLoader)
    
    initial_time = int(osm_full_yaml["_admin"]["created"])
    for id in list(osm_full_yaml["vcaStatus"].keys()):
        for app in list(osm_full_yaml["vcaStatus"][id]["applications"].keys()):
            final = osm_full_yaml['vcaStatus'][id]['applications'][app]['status']['since']
            final_parsed = parser.parse(final)
            final_timestamp = time.mktime(final_parsed.timetuple())
            data = {"iteration":count,
                    "appName":app,
                    "initial":initial_time,
                    "final":final_timestamp,
                    "delta":final_timestamp-initial_time}
            osm_data.append(data)
            
    
def write_parsed_data(file_name,data):
    with open(file_name,"w+") as outfile:
        firstLine = True
        for iteration in data:
            fields = iteration.pop("fields")
            if firstLine:
                outfile.write(",".join(fields)+"\n")
                firstLine = False
            outfile.write(",".join([str(val) for val in iteration.values()])+"\n")
            
def write_osm_data(file_name,data):
    with open(file_name,"w+") as outfile:
        fields = list(data[0].keys())
        #firstline
        outfile.write(",".join(fields)+"\n")
        for app in data:
            outfile.write(",".join([str(val) for val in app.values()])+"\n")
def main():
    # Iterate dump directories
    # Using re and dirlisting to avoid having to know how many dumps there are
    main_ns_data = []
    charmed_ns_data = []
    mep_data = []
    osm_data = []
    count=0
    operation = "scale"
    for dumpdir in sorted(os.listdir(), key=lambda x:int(x.split("_")[-1]) if re.match("^results.*", x) else -1):
        try:
            if re.match("^results.*", dumpdir):
                print(dumpdir)
                if operation == "scale":
                    with open(f"{dumpdir}/dump_pod1/ns") as file:
                       for line in file.readlines():
                           if "b'scale" in line:
                               print(line) 
                else:
                    # enter directory and iterate known dumps
                    pod_dump(dumpdir,main_ns_data,charmed_ns_data,mep_data,count)
                    #osm_yaml(dumpdir,osm_data,count)
                    count+=1
        except Exception as e:
           print(e)
           print(f"Iteration {dumpdir} had an unexpected error please manually remove the directory")

    #write_parsed_data("main_ns_data.csv",main_ns_data)
    #write_parsed_data("charmed_ns_data.csv",charmed_ns_data)
    #write_parsed_data("mep_data.csv",mep_data)
    # different file easier than creating something proper since this is single use
    #write_osm_data("osm_data.csv",osm_data)

if __name__ == "__main__":
    main()