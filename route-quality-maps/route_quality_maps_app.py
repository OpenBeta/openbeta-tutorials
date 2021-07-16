import numpy as np
import pandas as pd
import plotly.graph_objects as go
from grade_rank_calculation import calculate_grade_rank

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

DF = pd.read_pickle('RouteQualityData.pkl.zip', compression='zip')
AT = open('.mapbox_token').read()

app = dash.Dash(__name__)
input_types = ['text', 'number']
input_ids = ['metric', 'metric_threshold', 'route_type', 'grade_range']

app.layout = html.Div([
    html.Div([
        html.Label('Route Type:'),
        dcc.Dropdown(
            id='route_type',
            options=[{'label': 'Trad', 'value': 'trad'},
                     {'label': 'Sport', 'value': 'sport'},
                     {'label': 'All', 'value': 'all'}],
            style={'width':'40%'},
            value='All'),
        html.Label('Route Quality Metric:'),
        dcc.Dropdown(
            id='metric',
            options=[{'label': 'Mean Stars', 'value': 'mean_rating'},
                     {'label': 'Median Stars', 'value': 'median_rating'},
                     {'label': 'Mean RQI', 'value': 'RQI_mean'},
                     {'label': 'Median RQI', 'value': 'RQI_median'},
                     {'label': 'Mean ARQI', 'value': 'ARQI_mean'},
                     {'label': 'Median ARQI', 'value': 'ARQI_median'}],
            style={'width':'40%'},
            value='Mean Stars'),
        dcc.Input(
            id='metric_threshold',
            type='number',
            min=0.0, max=4.0, step=0.5,
            placeholder='Min Route Quality',
            style={'width': '12%'}),
        dcc.Input(
            id='min_grade',
            type='text',
            placeholder='Min Grade'),
        dcc.Input(
            id='max_grade',
            type='text',
            placeholder='Max Grade'),
        html.Button('Submit', id='button')
    ]),
    html.Br(),
    dcc.Graph(id='mymap'),
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
    
    cols = ['route_name', 'type_string', 'nopm_YDS', 'safety', metric]        
    df_agg = df.groupby('sector_ID')['route_name', 'type_string', 'nopm_YDS', 'safety', metric].agg(lambda x: list(x))
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
    
    df_agg['hover'] = df_agg['parent_sector'] + '<br>' + \
                      df_agg['num_routes'].astype(str) + ' routes' + '<br>' + \
                      df_agg['NRGT'].astype(str) + ' routes > ' + str(metric_threshold) + ' stars'
    
    sizenorm = max(df_agg['NRGT'])
    df_agg['size'] = 0
    sizes = np.linspace(0, sizenorm, num=6)
    size_limits = [(sizes[i], sizes[i+1], (i+1)*7) for i in range(len(sizes)-1)]
    
    for ll,hl,size in size_limits:
        df_agg.loc[(df_agg['NRGT'] >= ll) & (df_agg['NRGT'] < hl), 'size'] = size
            
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
                      colorbar_title='# Routes > Min'),
        hovertext=df_agg['hover'],
        hoverinfo='text',
        hoverlabel=dict(font_size=12,
                        font_family='Arial')
        )
    
    layout = dict(margin=dict(l=0, t=0, r=0, b=0, pad=0),
                  mapbox=dict(center=dict(lat=39,lon=-95),
                              style='light',
                              zoom=3.5,
                              accesstoken=AT),
                  geo=dict(scope='usa',
                           projection_type='albers usa'))
    
    fig = go.Figure(data=data, layout=layout)    
    fig.write_html('test.html')

    return fig

if __name__ == '__main__':
    app.run_server(debug=True, port=5000)
