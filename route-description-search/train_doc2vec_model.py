import re
import string
import pickle
import gensim
import collections
import random
import pandas as pd
import numpy as np
from nltk import word_tokenize
from gensim.parsing.preprocessing import remove_stopwords


def read_corpus(df):

    """
        read corpus from df, clean each description as it is read
    """

    count = -1
    for i, data in df.iterrows():

        count += 1
        desc = ' '.join(data.description)

        desc = str(desc).lower()  # lowercase
        desc = remove_stopwords(desc)
        desc = re.sub(r'\s+', ' ', desc)  # multiple spaces converted to single spaces
        desc = re.sub('[0-9]', '', desc)  # remove digits
        desc = re.sub(r'(?<=\w)-(?=\w)', ' ', desc)  # dash replaced with space
        desc = re.sub(f'[{re.escape(string.punctuation)}]', '', desc)  # remove punctuation and special characters

        tokens = word_tokenize(desc)
        tokens = [t for t in tokens if len(t) > 1]  # remove short tokens

        yield gensim.models.doc2vec.TaggedDocument(tokens, [count])


def clean_desc(desc):

    """
        cleans descriptions
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


if __name__ == '__main__':

    # read data and remove routes with no description
    df = pd.read_pickle('Curated_OpenBetaAug2020_RytherAnderson.pkl.zip', compression='zip')
    df_desc = df[['route_name', 'route_ID', 'type_string', 'description']]
    mask = (df['description'].str.len() > 0)
    df_desc = df_desc[mask]
    print(len(df_desc.index), 'initial descriptions')
    print()

    # convert to corpus
    train_corpus = list(read_corpus(df_desc))  # documents are tagged for training, i.e. tokens_only=False
    docID_2_rID = dict((i, rID) for i, rID in enumerate(df_desc.route_ID))

    # train and save the model
    # upped the epochs from typical 10-20 since the descriptions are relatively short
    model = gensim.models.doc2vec.Doc2Vec(vector_size=50, min_count=2, epochs=80, window=10) 
    model.build_vocab(train_corpus)
    print('training...')
    model.train(train_corpus, total_examples=model.corpus_count, epochs=model.epochs)
    print('saving...')
    print()
    model.save('doc2vec.model')

    with open('docID_2_routeID.pkl', 'wb') as rIDmap:
        pickle.dump(docID_2_rID, rIDmap)

    # sanity check against training data
    print('SANITY CHECK AGAINST TRAINING DATA:')
    print('------------------------------------')
    ranks = []
    samples = random.sample(range(len(train_corpus)), 1000)  # 1000 random samples from the training data

    for doc_id in samples:
        inferred_vector = model.infer_vector(train_corpus[doc_id].words)  # get the inferred vector for the training doc
        sims = model.dv.most_similar([inferred_vector], topn=len(model.dv))  # calculate the most similar docs (the doc itself should be in this)
        rank = [ID for ID, sim in sims].index(doc_id)  # calculate the rank the document is to itself (rank 0 means it is most similar to itself)
        ranks.append(rank)  # list the ranks

    counter = collections.Counter(ranks)
    ranks = counter.most_common()
    ranks = sorted(ranks, key=lambda x: x[0])

    print('{:<10} {:<10} {:<15}'.format(*['rank', 'count', 'cumulative sum']))
    print('------------------------------------')
    for i, (rank, count) in enumerate(ranks):
        cumsum = np.sum([r[1] for r in ranks[0:i+1]])
        print('{:<10} {:<10} {:<15}'.format(*[rank, count, cumsum]))
    print('------------------------------------')
    print()

    # check against test descriptions
    with open('validation_phrases.txt', 'r') as td:
        test_descs = list(td)
    test_descs = [d.replace('\n','') for d in test_descs if d != '\n']
    test_desc_tokens = [clean_desc(desc) for desc in test_descs]

    print('TEST PHRASE COMPARISONS:')
    print('-----------------------------------------------------------------------------------------------------------------------')
    for desc, token in zip(test_descs, test_desc_tokens):

        inferred_vector = model.infer_vector(token)  # get the inferred vector for the test phrase
        sims = model.dv.most_similar([inferred_vector], topn=3)  # calculate the most similar docs (the doc itself should be in this)

        print('TEST:', '"' + desc + '"')
        for i, (doc_id, sim) in enumerate(sims):

            rID = docID_2_rID[doc_id]
            sim_desc = list(df_desc[df_desc.route_ID == rID]['description'])[0][0]

            line = ' '.join(['MOST SIMILAR', str(i) + ':', sim_desc])
            print(line)

        print('-----------------------------------------------------------------------------------------------------------------------')
