import matplotlib
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

N = 3

def open_csv_files(file_name,fields,func=None):
    with open(file_name,"r") as file:
        # ignore first line cause we know what it is
        first_line = file.readline().rstrip().split(",")
        csv_keys_indexs = {field:first_line.index(field) for field in fields}
        line = file.readline()
        retdata = dict.fromkeys(fields,None)
        while line:
            tmpdata = line.rstrip().split(",")
            for field in fields:
                if retdata[field]:
                    retdata[field].append(tmpdata[csv_keys_indexs[field]])
                else:
                    retdata[field]=[tmpdata[csv_keys_indexs[field]]]
            line = file.readline()
    return retdata

def replace_keys(data,replacement):
    for old_name,new_name in replacement:
        data[new_name] = data.pop(old_name)
    return data

def draw_diagram(data,fields,yaxis_title):

    fig = go.Figure()
    count = 0
    c = ['hsl('+str(h)+',50%'+',50%)' for h in np.linspace(0, 360, len(data.keys())+2)]
    for field in fields:
        fig.add_trace(go.Box(y=data[field], name=field,
                        marker_color = c[count]))
        count+=1
    fig.update_layout(
    yaxis_title=yaxis_title,
    boxmode='group' # group together boxes of the different traces for each value of x
    )
    fig.show()


def main():
    # Also replaces keys due to plotly not allowing much change from what isn't in the data source
    main_ns_data = open_csv_files("main_ns_data.csv",["delta0","delta1"])
    main_ns_data = replace_keys(main_ns_data,[("delta0","k8s-osm-cluster-ns"),("delta1","mec-env-ns")])
    draw_diagram(main_ns_data,fields=["k8s-osm-cluster-ns","mec-env-ns"],yaxis_title="Time in seconds")
    
    charmed_ns_data = open_csv_files("charmed_ns_data.csv",["delta0"])
    charmed_ns_data = replace_keys(charmed_ns_data,[("delta0","charmed-osm")])
    draw_diagram(charmed_ns_data,fields=["charmed-osm"],yaxis_title="Time in seconds")
    
    
    mep_data = open_csv_files("mec_dataV2.csv",["delta0","delta1","delta2","delta3"])
    mep_data = replace_keys(mep_data,[("delta0","Application Ready"),
                             ("delta1","Service Creation"),
                             ("delta2","Subscription Creation"),
                             ("delta3","Service Query")])
    draw_diagram(mep_data,fields=["Application Ready","Service Creation","Subscription Creation","Service Query"],yaxis_title="Time in seconds")
    

if __name__ == "__main__":
    main()