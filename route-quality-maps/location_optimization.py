import numpy as np
import pandas as pd
import plotly.graph_objects as go
from grade_rank_calculation import calculate_grade_rank
from mpu import haversine_distance
from scipy.optimize import differential_evolution
from multiprocessing import cpu_count

class location_optimizer(object):

    def __init__(self, df, starting_loc=np.array([39.5501, -105.7281]), metric='ARQI_median', 
                 route_type='all', grade_range='all'):

        if route_type != 'all':
            df = df[df['type_string'] == route_type].copy()
            
        if grade_range != 'all':
            lo,hi = grade_range.split('-')
            lo_rank = calculate_grade_rank(lo)
            hi_rank = calculate_grade_rank(hi)                
            df = df[(lo_rank <= df['YDS_rank']) & (df['YDS_rank'] <= hi_rank)].copy()

        df['parent_loc'] = df.apply(lambda row: np.array(row['parent_loc'][::-1]), axis=1)

        self.quals = df[metric]
        self.locs = df['parent_loc']
        
    def energy(self, quality, loc0, loc1, eps=1.0e-6):
    
        dist = haversine_distance(loc0, loc1) + eps
        return -quality/(dist*dist)
    
    def total_energy(self, loc):
        
        TE = 0.0

        for qual, pos in zip(self.quals, self.locs):
            TE += self.energy(qual, pos, loc)

        return TE

    def optimize(self):

        bounds = [(36.5,49), (-123.9157,-69.2246)]

        res = differential_evolution(self.total_energy, bounds, polish=True, disp=True)

        print(res)
 
df = pd.read_pickle('RouteQualityData.pkl.zip', compression='zip')
LO = location_optimizer(df, grade_range='5.13a-5.13b', route_type='sport')
LO.optimize()


