import os
import re
import csv

def read_ns(dir):
    # dump is in a weird state where each data isn't a line 
    # we can used the 'Received Message' to parse lines
    data = []
    tmp_data = None
    with open(dir,"r") as file:
        tmp_data = "\n".join(file.readlines()).split("Received message")
    # remove index 0 which is ''
    tmp_data.pop(0)
    ns_data = ["iteration","instance_start","instance_started","delta"]
    ns_values = [dir.split("/")[0].split("_")[-1]]
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
            
def read_mep(dir):
    # TODO MISSING INITIALIZED TIME FROM NS
    # Order of each mep received action
    mep_data = ["iteration","mep_initializaton","mec_app_ready","mec_app_service_creation","mec_app_subscriptions","mec_app_service_query"]
    mep_values = [dir.split("/")[0].split("_")[-1]]
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

def pod_dump(dir,main_ns_data,charmed_ns_data,mep_data):
    # iterate all known pod dirs and their files
    # Main OSM pod
    main_ns_data.append(read_ns(f"{dir}/dump_pod1/ns"))
    # Charmed OSM pod
    charmed_ns_data.append(read_ns(f"{dir}/dump_pod2/ns"))
    mep_data.append(read_mep(f"{dir}/dump_pod2/mep"))
        
def osm_yaml(dir):
    pass


def write_parsed_data(file_name,data):
    with open(file_name,"w+") as outfile:
        firstLine = True
        for iteration in data:
            fields = iteration.pop("fields")
            if firstLine:
                outfile.write(",".join(fields)+"\n")
                firstLine = False
            outfile.write(",".join([str(val) for val in iteration.values()])+"\n")
def main():
    # Iterate dump directories
    # Using re and dirlisting to avoid having to know how many dumps there are
    main_ns_data = []
    charmed_ns_data = []
    mep_data = []
    for dumpdir in os.listdir():
        if re.match("^results.*",dumpdir):
            # enter directory and iterate known dumps
            pod_dump(dumpdir,main_ns_data,charmed_ns_data,mep_data)
    
    """print(main_ns_data)
    print(charmed_ns_data)
    print(mep_data)"""
    
    write_parsed_data("main_ns_data",main_ns_data)
    write_parsed_data("charmed_ns_data",charmed_ns_data)
    write_parsed_data("mep_data",mep_data)

if __name__ == "__main__":
    main()