import matplotlib.pyplot as plt
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
                    retdata[field].append(float(tmpdata[csv_keys_indexs[field]]))
                else:
                    retdata[field]=[float(tmpdata[csv_keys_indexs[field]])]
            line = file.readline()
    return retdata

def replace_keys(data,replacement):
    for old_name,new_name in replacement:
        data[new_name] = data.pop(old_name)
    return data


def draw_diagram(data,fields,yaxis_title,title,filename,xaxis_range=None):
    final_data = [data[key] for key in data]
    fig = plt.figure(figsize =(10, 7))
    ax = fig.add_subplot(111)
    # Creating axes instance
    print(final_data)
    bp = ax.boxplot(final_data, patch_artist = True,
                    notch = False, vert = True)
    
    colors = ['#DAE8FC', '#D5E8D4',
        '#F8CECC', '#FFF2CC']
    
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
 
    # changing color and linewidth of
    # whiskers
    for whisker in bp['whiskers']:
        whisker.set(color ='#9673A6',
                    linewidth = 1.5,
                    linestyle =":")
    
    # changing color and linewidth of
    # caps
    for cap in bp['caps']:
        cap.set(color ='#8B008B',
                linewidth = 2)
    
    # changing color and linewidth of
    # medians
    for median in bp['medians']:
        median.set(color ='#F0A30A',
                linewidth = 3)
        
    # changing style of fliers
    for flier in bp['fliers']:
        flier.set(marker ='D',
                color ='#e7298a',
                alpha = 0.5)
        
    # x-axis labels
    ax.set_xticklabels(fields,fontsize=15)
    
    
    # Removing top axes and right axes
    # ticks
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    
    # quantiles
    quantiles = []
    for box in final_data:
        quantiles.append(np.quantile(box, np.array([0.25, 0.50, 0.75])))
    
    for idx,quantile_list in enumerate(quantiles):
        for quantile in quantile_list:
            plt.annotate(round(quantile,2),(idx+1.10,quantile))
        
    plt.ylabel('Time in seconds',fontsize=15)
    plt.title(title, fontdict={'family': 'normal', 'weight': 'bold', 'size': 17})
    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontsize(13)
    plt.ylim(xaxis_range)
    # show plot
    plt.tight_layout()
    plt.savefig(filename)
    plt.show()

def main():
    # Also replaces keys due to plotly not allowing much change from what isn't in the data source
    main_ns_data = open_csv_files("main_ns_data.csv",["delta0","delta1"])
    main_ns_data = replace_keys(main_ns_data,[("delta0","k8s-osm-cluster-ns"),("delta1","mec-env-ns")])
    draw_diagram(main_ns_data,fields=["k8s-osm-cluster-ns","mec-env-ns"],yaxis_title="Time in seconds",title="Deployment time of k8s-osm-cluster-ns and mec-env-ns NSs",xaxis_range=[570,730],filename="deploy_time_ns.pdf")
    
    charmed_ns_data = open_csv_files("charmed_ns_data.csv",["delta0"])
    charmed_ns_data = replace_keys(charmed_ns_data,[("delta0","charmed-osm")])
    draw_diagram(charmed_ns_data,fields=["charmed-osm"],yaxis_title="Time in seconds",title="Deployment time of k8s-charmed-osm-cluster",xaxis_range=[7,30],filename="osm-charmed.pdf")
    
    
    mep_data = open_csv_files("mec_dataV2.csv",["delta0","delta1","delta2","delta3"])
    mep_data = replace_keys(mep_data,[("delta0","Application Ready"),
                             ("delta1","Service Creation"),
                             ("delta2","Subscription Creation"),
                             ("delta3","Service Query")])
    draw_diagram(mep_data,fields=["Application Ready","Service Creation","Subscription Creation","Service Query"],yaxis_title="Time in seconds",title="MEC Application execution time",xaxis_range=[275,425],filename="mep.pdf")
    

if __name__ == "__main__":
    main()
