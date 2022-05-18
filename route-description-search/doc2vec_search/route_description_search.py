import re
import sys
import string
import math
import pickle
import gzip
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')
from gensim.parsing.preprocessing import remove_stopwords
from gensim.models import Doc2Vec
from nltk import word_tokenize
from geopy.geocoders import Nominatim


def clean_desc(desc):

    """
        cleans descriptions for use with doc2vec model
    """

    desc = str(desc).lower()  # lowercase
    desc = remove_stopwords(desc)
    desc = re.sub(r'\s+', ' ', desc)  # multiple spaces converted to single spaces
    desc = re.sub('[0-9]', '', desc)  # remove digits
    desc = re.sub(r'(?<=\w)-(?=\w)', ' ', desc)  # dash replaced with space
    desc = re.sub(f'[{re.escape(string.punctuation)}]', '', desc)  # remove punctuation and special characters

    tokens = word_tokenize(desc)
    tokens = [t for t in tokens if len(t) > 1]  # remove short tokens

    return tokens


def description_search(model, desc, routeID_key, route_data, topn=3):

    """
        model is the doc2vec model, desc is the description
        returns all the data (contained in route_data) for the topn routes
    """

    tokens = clean_desc(desc)
    inferred_vector = model.infer_vector(tokens, epochs=100)
    sims = model.dv.most_similar([inferred_vector], topn=topn)
    res = route_data[route_data['route_ID'].isin([routeID_key[x[0]]
                     for x in sims])].copy()
    res['similarity'] = [x[1] for x in sims]
    res['query'] = desc
    res.reset_index(drop=True, inplace=True)

    return res


def print_search_results(res):

    query = res['query'].unique()[0]
    N = len(res)

    print(f'Results for the query: "{query}"')
    print(f'{N} routes returned')
    print()

    for i, row in res.iterrows():

        grade = ' '.join([g for g in (row.YDS, row.Vermin) if g is not None])
        sim = np.round(row.similarity, 2)
        name = row.route_name
        desc = ' '.join(row.description)
        nc = len(desc)
        ceil = math.ceil(nc/100)
        lon, lat = row.parent_loc

        geolocator = Nominatim(user_agent='http')
        loc_str = f'{lat}, {lon}'
        location = geolocator.reverse(loc_str)
        display = location.raw['display_name']
        address = ','.join(display.split(',')[0:-2])

        print('-'*100)
        print(f'RESULT {i} (similarity = {sim}):')
        print(f'{name} ({grade}), {row.type_string}')
        print(address)
        print()
        print('DESCRIPTION:')
        for i in range(ceil):
            print(desc[i*100:(i+1)*100])
        print('-'*100)
        print()


if __name__ == '__main__':

    model = Doc2Vec.load('doc2vec.model')

    with gzip.open('search_data.pkl.zip', 'rb') as key:
        search_data = pickle.load(key)

    route_data = search_data['route_data']
    routeID_key = search_data['routeID_key']

    desc = sys.argv[1]
    res = description_search(model, desc, routeID_key, route_data)
    print_search_results(res)
