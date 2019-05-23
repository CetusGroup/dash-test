import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.plotly as py
from plotly.graph_objs import Layout, Figure, Scatter, Scatterpolar
from plotly.graph_objs import layout as playout
from plotly.graph_objs import scatter as pscatter
from scipy.stats import rayleigh
from flask import Flask
import numpy as np
import pandas as pd
import os
import sqlite3
import datetime as dt
from styles import *

app = dash.Dash(
    'streaming-wind-app',
#    stylesheets=['Css/skeleton.min.css']
#    external_stylesheets=external_css
)
server = app.server
app.title = 'Marine Group'
app.config['suppress_callback_exceptions'] = True


def create_winddirection_graph():
    return html.Div([
        html.Div([
            html.H5("Wind direction")
        ], className='Title'),
        html.Div([
            dcc.Graph(id='wind-direction'),
        ], className='twelve columns wind-direction'),
    ],
    className='row wind-polar-row',
    style=frame_style)


def create_windspeed_graph():
    return html.Div([
        html.Div([
            html.H5("Wind speed"),
        ], className='Title'),
        html.Div([
            dcc.Graph(id='wind-speed'),
        ], className='twelve columns wind-speed'),
        dcc.Interval(id='wind-speed-update', interval=4000, n_intervals=0),
    ],
    className='row wind-speed-row',
    style=frame_style)


app.layout = dcc.Tabs(id="tabs", children=[
    dcc.Tab(label='Wind', children=[
            html.Table(
                html.Tr([
                    html.Td(create_winddirection_graph(), style={'width': '25%'}),
                    html.Td(create_windspeed_graph(), style={'width': '75%'})
                ]),
            )
        ],
        style=tab_style,
        selected_style=tab_selected_style
    ),

    dcc.Tab(label='Water', children=[
            dcc.Graph(
                id='example-graph-1',
                figure={
                    'data': [
                        {'x': [1, 2, 3], 'y': [1, 4, 1],
                            'type': 'bar', 'name': 'Ra1'},
                        {'x': [1, 2, 3], 'y': [1, 2, 3],
                            'type': 'bar', 'name': 'Ra2'},
                    ]
                }
            )
        ],
        style=tab_style,
        selected_style=tab_selected_style
    ),

    dcc.Tab(label='Oil', children=[
            dcc.Graph(id='example-graph-2')
        ],
        style=tab_style,
        selected_style=tab_selected_style
    ),

    dcc.Tab(label='Other', style=tab_style, selected_style=tab_selected_style),
],
style={'height': '30px'})


@app.callback(Output('wind-speed', 'figure'), [Input('wind-speed-update', 'n_intervals')])
def gen_wind_speed(interval):
    now = dt.datetime.now()
    sec = now.second
    minute = now.minute
    hour = now.hour

    total_time = (hour * 3600) + (minute * 60) + (sec)

    con = sqlite3.connect("./Data/wind-data.db")
    df = pd.read_sql_query('SELECT Speed, SpeedError, Direction from Wind where\
                            rowid > "{}" AND rowid <= "{}";'
                            .format(total_time-200, total_time), con)

    trace = Scatter(
        y=df['Speed'],
        line=pscatter.Line(color='#42C4F7'),
        hoverinfo='skip',
        error_y=pscatter.ErrorY(
            type='data',
            array=df['SpeedError'],
            thickness=1.5,
            width=2,
            color='#B4E8FC'
        ),
        mode='lines'
    )

    layout = Layout(
        height=450,
        xaxis=dict(
            range=[200, 0],
            showgrid=False,
            showline=False,
            zeroline=False,
            fixedrange=True,
            tickvals=[0, 50, 100, 150, 200],
            ticktext=['200', '150', '100', '50', '0'],
            title='Time Elapsed (sec)'
        ),
        yaxis=dict(
            range=[min(0, min(df['Speed'])),
                   max(45, max(df['Speed'])+max(df['SpeedError']))],
            showline=False,
            fixedrange=True,
            zeroline=False,
            nticks=max(6, round(df['Speed'].iloc[-1]/10))
        ),
        margin=playout.Margin(t=45, l=50, r=45)
    )

    return Figure(data=[trace], layout=layout)


@app.callback(Output('wind-direction', 'figure'), [Input('wind-speed-update', 'n_intervals')])
def gen_wind_direction(interval):
    now = dt.datetime.now()
    sec = now.second
    minute = now.minute
    hour = now.hour

    total_time = (hour * 3600) + (minute * 60) + (sec)

    con = sqlite3.connect("./Data/wind-data.db")
    df = pd.read_sql_query("SELECT * from Wind where rowid = " +
                                         str(total_time) + ";", con)
    val = df['Speed'].iloc[-1]
    direction = [0, (df['Direction'][0]-7), (df['Direction'][0]+7), 0]

    fcolor0 = '#%2x80%2x' % (0x84+2*int(val), 0x86-2*int(val))
    fcolor1 = '#%2x80%2x' % (0x84+2*int(val), 0x86-2*int(val))
    fcolor2 = '#%2x80%2x' % (0x84+2*int(val), 0x86-2*int(val))

    trace0 = Scatterpolar(
        r=[0, val, val, 0],
        theta=direction,
        mode='lines',
        fill='toself',
        fillcolor=fcolor0,
        line=dict(color='rgba(32, 32, 32, .6)', width=1)
    )

    trace1 = Scatterpolar(
        r=[0, val*0.65, val*0.65, 0],
        theta=direction,
        mode='lines',
        fill='toself',
        fillcolor='#C7D9F9',
        line=dict(color='rgba(32, 32, 32, .6)', width=1)
    )

    trace2 = Scatterpolar(
        r=[0, val*0.3, val*0.3, 0],
        theta=direction,
        mode='lines',
        fill='toself',
        fillcolor='#DBDCFC',
        line=dict(color='rgba(32, 32, 32, .6)', width=1)
    )

    layout = Layout(
        autosize=True,
        width=360,
        margin=playout.Margin(t=10, b=10, r=20, l=20),
        polar=dict(
            bgcolor='#F2F2F2',
            radialaxis=dict(range=[0, 60], angle=0, dtick=10),
            angularaxis=dict(showline=False, tickcolor='white')
        ),
        showlegend=False,
    )

    return Figure(data=[trace0, trace1, trace2], layout=layout)


if __name__ == '__main__':
    app.run_server()
