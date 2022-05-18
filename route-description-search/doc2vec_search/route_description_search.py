import re
import string
import math
import pickle
import gzip
import pandas as pd
import numpy as np
import warnings
import argparse

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

    tokens = clean_desc(desc)  # get the cleaned description
    inferred_vector = model.infer_vector(tokens, epochs=1000)  # convert to a vector
    sims = model.dv.most_similar(positive=[inferred_vector], topn=topn)
    res = pd.DataFrame()
    route_data.route_ID = route_data.route_ID.astype(int)

    for doc_id, score in sims:  # make sure the routes are in the correct order

        route_id = routeID_key[doc_id]
        route = route_data.query(f'route_ID == {route_id}').copy()
        route['score'] = score
        res = pd.concat([res, route])

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
        sim = np.round(row.score, 2)
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

    parser = argparse.ArgumentParser(description='Arguments for running the doc2vec search')
    parser.add_argument('-d', action='store', dest='desc', type=str,
                        required=False, default='guano', help='a hypothetical route description')
    parser.add_argument('-n', action='store', dest='topn', type=int,
                        required=False, default=3, help='the number of results to return')
    args = parser.parse_args()

    model = Doc2Vec.load('doc2vec.model')

    with gzip.open('search_data.pkl.zip', 'rb') as key:
        search_data = pickle.load(key)

    route_data = search_data['route_data']
    routeID_key = search_data['routeID_key']

    res = description_search(model, args.desc, routeID_key, route_data, topn=args.topn)
    print_search_results(res)
