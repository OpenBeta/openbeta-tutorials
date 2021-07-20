import numpy as np
import pandas as pd
import plotly.graph_objects as go
from grade_rank_calculation import calculate_grade_rank

AT = open('.mapbox_token').read()

def route_quality_map_with_filters(df, fname='quality_map', metric='ARQI_median', metric_threshold=3.0, route_type='all', grade_range='all'):
    
    if route_type != 'all':
        df = df[df['type_string'] == route_type].copy()
        
    if grade_range != 'all':
        lo,hi = grade_range.split('-')
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
        df_agg.loc[(df_agg['NRGT'] >= ll) & (df_agg['NRGT'] < hl), 'size'] = size
            
    data = go.Scattermapbox(
        lat = df_agg['lat'],
        lon = df_agg['lon'],
        mode='markers',
        marker = dict(size=df_agg['size'],
                      color=df_agg['NRGT'],
                      reversescale=False,
                      cmin= 0,
                      cmax=sizenorm-0.10*sizenorm,
                      colorscale='Inferno',
                      colorbar_title='# Routes > Threshold'),
        customdata=np.c_[df_agg['parent_sector'], df_agg['num_routes'], df_agg['NRGT'], df_agg['best_route']],
        hoverlabel=dict(font_size=12,
                        font_family='Arial',
                        bgcolor='white'),
        hovertemplate=
        '<b>%{customdata[0]}</b><br>' +
        'Total Routes: %{customdata[1]}<br>' +
        'Routes > Min Quality: %{customdata[2]}<br><br>' +
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
                  geo = dict(scope='usa',
                             projection_type='albers usa',
                             resolution=110))
    
    fig = go.Figure(data=data, layout=layout)
    fig.write_html(fname + '.html')

if __name__ == '__main__':

    df = pd.read_pickle('RouteQualityData.pkl.zip', compression='zip')
    route_quality_map_with_filters(df, metric='ARQI_median', metric_threshold=3.5, route_type='sport', grade_range='5.13a-5.13c')
