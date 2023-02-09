import os
import json
import base64
import dash
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objs as go

import numpy as np
import scipy.stats as st
import statistics

def plot_line(data, labels, title, **kwargs):
    df = pd.DataFrame(data)

    fig = px.line(df, x=labels[0], y=labels[1], title=title)
    fig.update_layout(clickmode="event+select")
    return fig


def plot_bars(data, labels, title, color=None, **kwargs):
    df = pd.DataFrame(data)

    fig = px.bar(df, x=labels[0], y=labels[1], color=color, title=title)
    for fig_data in fig.data:
        fig_data.marker.line.color = fig_data.marker.color

    fig.update_layout(clickmode="event+select")
    return fig


def plot_hist(data, labels, title, color=None, **kwargs):
    df = pd.DataFrame(data)

    fig = px.box(df, x=labels[0], y=labels[1], color=color, title=title, **kwargs)
    fig.update_layout(clickmode="event+select")
    return fig

def box_plot(data, labels, title, color=None, **kwargs):
    df = pd.DataFrame(data)

    fig = px.box(df, x=labels[0], y=labels[1], color=color, title=title, **kwargs)      #, points="all"
    fig.update_layout(clickmode="event+select")
    return fig

def __remove_outliers(values):
    # !! Be carefull with this, it's very close to the confidence but not really the confidence interval !!
    # perfectly fine for a quick and dirty outlier detection/removal, anything else requires proper calculation
    avg = statistics.mean(values)
    sigma = statistics.stdev(values)

    lower_thr = avg - (2 * sigma)   # use 2*sigma for near 95%, 3*sigma for near 99%
    higher_thr = avg + (2 * sigma)
    print(lower_thr, higher_thr)
    out = list()
    for i in values:
        if i < lower_thr or i > higher_thr:
            continue
        out.append(i)
    return out

DATA_LOCATIONS = {
    "mec-env-ns": "mec_env_ns/main_ns_data.csv",
    "mec-app-ns": "mec_app_ns/mec_app_ns.csv",
    "scale-out": "scaling/scaling_ns_data.csv",
    "scale-in": "scaling/scaling_ns_data.csv",
    "base-vnf": "base_tests/results_base_vnf/base_data.csv",
    "base-cnf": "base_tests/results_base_cnf/base_data.csv",
}

def main(logs_path):
    external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    styles = {
        "pre": {
            "border": "thin lightgrey solid",
            "overflowX": "scroll",
        },
        "row": {"display": "flex", "justifyContent": "center"},
    }
    
    data_location = {
        "Deployment time of mec-env-ns NS": "mec-env-ns",
        "Deployment time of mec-app-ns NS": "mec-app-ns",
        "Deployment time of base-vnf-ns NS": "base-vnf",
        "Deployment time of base-cnf-ns NS": "base-cnf",
        "Scale-out time of the worker VDU of the k8s-cluster-vnf VNF": "scale-out",
        "Scale-in time of the worker VDU of the k8s-cluster-vnf VNF": "scale-in",
    }

    app.layout = html.Div(
        [
            html.Div(
                [
                    "Choose the data to process",
                    dcc.Dropdown(
                        id="data_location",
                        options=[
                            {"label": k, "value": v} for k, v in data_location.items()
                        ],
                    ),
                ]
            ),
            html.Div(
                [
                    "Choose the plot",
                    dcc.Dropdown(
                        id="plot_list",
                        options=[
                            {"label": "Box Plot", "value": "box"},
                        ],
                    ),
                ]
            ),
            html.Div(
                [
                    "Width",
                    dcc.Slider(
                        id="slider_width",
                        min=200,
                        max=2100,
                        step=25,
                        value=500,
                        marks={x: str(x) for x in range(200, 2100, 100)},
                    ),
                ]
            ),
            html.Div(
                [
                    "Height",
                    dcc.Slider(
                        id="slider_height",
                        min=200,
                        max=1000,
                        step=25,
                        value=600,
                        marks={x: str(x) for x in range(200, 1000, 100)},
                    ),
                ]
            ),
            html.Div(
                [
                    "Confidence Interval",
                    dcc.Input(
                        id="confidence_interval",
                        type="number",
                        min=0,
                        max=100,
                        step=1,
                        value=99,
                    ),
                ]
            ),
            html.Div(
                [
                    html.Button("Save as PDF", id="render_option", n_clicks=0),
                ]
            ),
            dcc.Graph(
                id="graph",
                config={
                    "editable": True,
                    "toImageButtonOptions": {"scale": 3, "format": "svg"},
                },
            ),
        ]
    )

    @app.callback(
        Output("graph", "figure"),
        Input("plot_list", "value"),
        Input("data_location", "value"),
        Input("slider_width", "value"),
        Input("slider_height", "value"),
        Input("confidence_interval", "value"),
        Input("render_option", "n_clicks"),
        State("data_location","options"),
    )
    def update_graphics(plot_type, data_location, width, height, confidence_interval, render_option, options):
        # if plot_type is None or file_name is None or width is None or height is None or render_option is None:
        #    return dcc.Graph()
        file_name = DATA_LOCATIONS[data_location]
        title = [x['label'] for x in options if x['value'] == data_location][0]

        data_plot = dict()
        additional_params = dict()

        data = []
        delta_index = 3
        if data_location.split("-")[0] == "scale" and data_location.split("-")[1] == "in":
            delta_index = 6
        with open(file_name, "r") as file:
            for line in file.readlines()[1:]:
                data_line = line.rstrip().split(',')
                print(data_line[0])
                if data_line[0].isnumeric():
                    data.append(float(data_line[delta_index]))

        print(data)
        time_key = "Time (s)"
        ns_key = "NS" if title.split(" ")[0] == "Deployment" else "Operation"

        data_plot = {
            ns_key: [],
            time_key: [],
        }
        print(data)
        ci = st.t.interval(alpha=int(confidence_interval)/100, df=len(data)-1, loc=np.mean(data), scale=st.sem(data))
        print(ci)
        data = [d for d in data if d > ci[0] and d < ci[1]]
        #data = __remove_outliers(data)
        print(len(data))
        data_plot[time_key] = data
        data_plot[ns_key] = [data_location]*len(data)

        if plot_type == "box":
            fig = box_plot(
                data_plot, list(data_plot.keys()), title=title, **additional_params
            )

        fig.update_layout(width=int(width), height=int(height))

        if render_option > 0:
            fig.write_image(
                f"images/{plot_type}_{file_name.split('/')[1].split('.')[0]}.pdf"
            )
            print("Image saved")

        return fig

    return app


if __name__ == "__main__":
    logs_path = "data"
    app_ = main(logs_path)
    app_.run_server(debug=True, host="127.0.0.1")
