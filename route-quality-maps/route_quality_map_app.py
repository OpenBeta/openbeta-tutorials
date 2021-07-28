import numpy as np
import pandas as pd
import plotly.graph_objects as go
from grade_rank_calculation import calculate_grade_rank
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from flask import Flask

DF = pd.read_pickle('RouteQualityData.pkl.zip', compression='zip')
AT = open('.mapbox_token').read()

server = Flask(__name__)
app = dash.Dash(server=server)

SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '14rem',
    'padding': '2rem 1rem',
    'margin-top': '4rem',
    'margin-bottom': '1rem',
    'margin-left': '0.75rem',
    'background-color': '#dce3f9',
    'font-family': 'Helvetica',
    'boxShadow': '#7491e9 4px 4px 2px',
    'border-radius': '10px'
}

MAP_STYLE = {
    'margin-top': '2rem',
    'margin-left': '16rem',
    'margin-right': '2rem',
    'padding': '2rem 1rem',
    'background-color': 'white',
}

TAB_STYLE = {
    'background-color': 'white',
    'align-items': 'center',
    'justify-content': 'center',
    'padding':'4px',
    'font-family': 'Helvetica',
    'height': '5vh'
}

TUTORIAL_STYLE = {
    'font-family': 'Helvetica',
}

sidebar = html.Div([
        
    html.H2('Filters', className='display-4'),
    html.Hr(),
    html.P('Subset routes by type, range of difficulty, and minimum quality (0-4 stars)', className='lead'),

    dbc.Col([
        html.Label('Route Type:'),
        dbc.Row(dcc.Dropdown(
            id='route_type',
            options=[{'label': 'Trad', 'value': 'trad'},
                     {'label': 'Sport', 'value': 'sport'},
                     {'label': 'All', 'value': 'all'}],
            style={'width':'91%'},
            value='All')),
        html.Br(),
        html.Label('Route Quality Metric:'),
        dbc.Row(dcc.Dropdown(
            id='metric',
            options=[{'label': 'Mean Stars', 'value': 'mean_rating'},
                     {'label': 'Median Stars', 'value': 'median_rating'},
                     {'label': 'Mean RQI', 'value': 'RQI_mean'},
                     {'label': 'Median RQI', 'value': 'RQI_median'},
                     {'label': 'Mean ARQI', 'value': 'ARQI_mean'},
                     {'label': 'Median ARQI', 'value': 'ARQI_median'}],
            style={'width':'91%'},
            value='Mean Stars')),
        html.Br(),
        html.Label('Minimum Route Quality: '),
        dbc.Row(dcc.Input(
            id='metric_threshold',
            type='number',
            min=0.0, max=4.0, step=0.5,
            placeholder=3.0,
            style={'width': '80%'})),
        html.Br(),
        html.Label(' Min Grade (YDS): '),
        dbc.Row(dcc.Input(
            id='min_grade',
            type='text',
            placeholder='5.10a',
            style={'width': '80%'})),
        html.Br(),
        html.Label(' Max Grade (YDS): '),
        dbc.Row(dcc.Input(
            id='max_grade',
            type='text',
            placeholder='5.11a',
            style={'width': '80%'})),
        html.Br(),
        html.Button('Submit', id='button')
    ])
], style=SIDEBAR_STYLE)

tutorial = html.Div([
    html.H2('Route Quality Metric Descriptions', className='display-4'),
    html.Hr(),
    html.P('Descriptions coming soon', className='lead'),
    html.H2('Known Gaps in the Data', className='display-4'),
    html.Hr(),
    html.P('These are the known gaps and inconsistencies in the current OpenBeta dataset, \
            taken from Mountain Project in August 2020.', className='lead'),
    html.Ul([html.Li('Bouldering user rating data is missing in the current dataset.'),
             html.Li('Wyoming user rating data (for all climb types) is also missing. \
                For now: Ten Sleep or Wild Iris in the Summer/Fall, Sinks Canyon in the Winter, \
                Vedauwoo if you like pain, and Cirque of Towers if you do cardio.'),
             html.Li('Some route names and/or grades have changed since the data was collected.'),
             html.Li('Snow, mixed (as in ice/rock), ice climbs, and non-technical climbs are omitted (on purpose).') 
            ])
], style=TUTORIAL_STYLE)

content = html.Div([dcc.Graph(id='mymap', 
                              figure={
                              'layout': go.Layout(xaxis={'showgrid': False, 'zeroline': False, 'visible': False}, 
                                                  yaxis={'showgrid': False, 'zeroline': False, 'visible': False})
                              })], 
    style=MAP_STYLE)

app.layout = html.Div([
                dcc.Tabs([
                    dcc.Tab([sidebar, content], label='Map', 
                        style={'padding': '0','line-height': '5vh'}, 
                        selected_style={'padding': '0','line-height': '5vh', 'background-color': '#dce3f9'}), 
                    dcc.Tab(tutorial, label='Tutorial', 
                        style={'padding': '0','line-height': '5vh'},
                        selected_style={'padding': '0','line-height': '5vh', 'background-color': '#dce3f9'})
                    ], style=TAB_STYLE)
                ])

@app.callback(
    Output(component_id='mymap', component_property='figure'),
    [Input(component_id='button', component_property='n_clicks')],
    [State(component_id='route_type', component_property='value'),
     State(component_id='metric', component_property='value'),
     State(component_id='metric_threshold', component_property='value'),
     State(component_id='min_grade', component_property='value'),
     State(component_id='max_grade', component_property='value')],
)

def update_map(n_clicks, route_type, metric, metric_threshold, min_grade, max_grade):

    if not n_clicks:
       raise PreventUpdate

    if route_type is None:
        route_type = 'all'

    if metric is None:
        metric = 'RQI_mean'

    if metric_threshold is None:
        metric_threshold = 3.5

    if min_grade is None:
        min_grade = '5.6'

    if max_grade is None:
        min_grade = '5.15a'

    df = DF.copy()

    if route_type != 'all':
        df = df[df['type_string'] == route_type].copy()
     
    lo, hi = min_grade, max_grade
    lo_rank = calculate_grade_rank(lo)
    hi_rank = calculate_grade_rank(hi)                
    df = df[(lo_rank <= df['YDS_rank']) & (df['YDS_rank'] <= hi_rank)].copy()
    
    cols = ['route_name', 'nopm_YDS', 'safety', metric]        
    df_agg = df.groupby('sector_ID')['route_name', 'nopm_YDS', 'safety', metric].agg(lambda x: list(x))
    df_agg.columns = cols

    df_agg['sector_ID'] = df_agg.index
    df_agg.index = range(len(df_agg.index))
    name_loc = df[['parent_sector', 'sector_ID', 'parent_loc']].copy()
    name_loc = name_loc.drop_duplicates(subset=['sector_ID'])
    df_agg = pd.merge(df_agg, name_loc, on='sector_ID')
    
    df_agg['num_routes'] = df_agg.apply(lambda row: len(row['route_name']), axis=1)
    df_agg['NRGT'] = df_agg.apply(lambda row: len([r for r in row[metric] if r >= metric_threshold]), axis=1)
    df_agg['lat'] = df_agg.apply(lambda row: row['parent_loc'][1], axis=1)
    df_agg['lon'] = df_agg.apply(lambda row: row['parent_loc'][0], axis=1)
    df_agg['best_route'] = df_agg.apply(lambda row: 
      [(n, np.round(m,2), g) for n,m,g in zip(row['route_name'],row[metric],row['nopm_YDS']) 
      if m == max(row[metric])][0], axis=1)
    
    sizenorm = max(df_agg['NRGT'])
    df_agg['size'] = 0
    sizes = np.linspace(0, sizenorm, num=6)
    size_limits = [(sizes[i], sizes[i+1], (i+1)*7) for i in range(len(sizes)-1)]
    
    for ll,hl,size in size_limits:
        df_agg.loc[(df_agg['NRGT'] > ll) & (df_agg['NRGT'] <= hl), 'size'] = size
    df_agg.loc[df_agg['NRGT'] == 0, 'size'] = 5
            
    data = go.Scattermapbox(
        lat = df_agg['lat'],
        lon = df_agg['lon'],
        mode='markers',
        marker = dict(size=df_agg['size'],
                      color=df_agg['NRGT'],
                      reversescale=False,
                      cmin=0,
                      cmax=sizenorm-0.10*sizenorm,
                      colorscale='Inferno',
                      colorbar_title='# Routes<br>\u2265 Min'),
        customdata=np.c_[df_agg['parent_sector'], 
                         df_agg['num_routes'],
                         df_agg['NRGT'],
                         df_agg['best_route']],
        hovertemplate=
        '<b>%{customdata[0]}</b><br>' +
        'Total Routes: %{customdata[1]}<br>' +
        'Routes \u2265 Min Quality: %{customdata[2]}<br><br>' +
        '<b>Best Route</b><br>' + 
        'Name: %{customdata[3][0]}<br>' +
        'Grade: %{customdata[3][2]}<br>' +
        'Rating: %{customdata[3][1]} stars' +
        '<extra></extra>'
        )
    
    layout = dict(margin=dict(l=0, t=0, r=0, b=0, pad=0),
                  mapbox=dict(center=dict(lat=39,lon=-95),
                              style='light',
                              zoom=3.5,
                              accesstoken=AT),
                  geo=dict(scope='usa',
                           projection_type='albers usa'))
    
    fig = go.Figure(data=data, layout=layout)    

    return fig

if __name__ == '__main__':
    #app.run_server()
    app.run_server(port=8000)
