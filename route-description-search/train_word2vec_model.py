import re
import string
import gensim
import pandas as pd
from nltk import word_tokenize
from gensim.parsing.preprocessing import remove_stopwords
from gensim.models import Phrases
from gensim.models.phrases import Phraser


def read_sentences(df, keep_stopwords=True):
    
    """
        read corpus from df, clean each description as it is read
    """
    
    for i, data in df.iterrows():
        
        desc = ' '.join(data.description)
        desc = str(desc).lower()  # lowercase
        
        if not keep_stopwords:
            desc = remove_stopwords(desc)
            
        desc = re.sub(r'\s+', ' ', desc)  # multiple spaces converted to single spaces
        desc = re.sub('[0-9]', '', desc)  # remove digits
        desc = re.sub(r'(?<=\w)-(?=\w)', ' ', desc)  # dash replaced with space
        sentences = desc.split('. ')

        for sentence in sentences:
        
            sentence = re.sub(f'[{re.escape(string.punctuation)}]', '', sentence)  # remove punctuation and special characters
            tokens = word_tokenize(sentence)
            tokens = [t for t in tokens if len(t) > 1]  # remove short tokens

            yield tokens


if __name__ == '__main__':

    df = pd.read_pickle('Curated_OpenBetaAug2020_RytherAnderson.pkl.zip', compression='zip')
    df_desc = df[['route_name', 'route_ID', 'type_string', 'description']]
    mask = (df['description'].str.len() > 0)
    df_desc = df_desc[mask]
    print(len(df_desc.index), 'initial descriptions')
    print()

    sw_sentences = list(read_sentences(df, keep_stopwords=True))
    nsw_sentences = list(read_sentences(df, keep_stopwords=False))
    
    bigram = Phrases(sw_sentences, min_count=5, threshold=100)
    trigram = Phrases(bigram[sw_sentences], threshold=10)
    bigram_mod = Phraser(bigram)
    trigram_mod = Phraser(trigram)
    
    sentences = [bigram_mod[sent] for sent in nsw_sentences]
    sentences = [trigram_mod[bigram_mod[sent]] for sent in sentences]
    
    model = gensim.models.word2vec.Word2Vec(min_count=10, window=5, vector_size=50)
    model.build_vocab(sentences)
    print(len(model.wv), 'words in the vocab')

    print('training...')
    model.train(sentences, total_examples=model.corpus_count, epochs=10)
    print('saving...')
    print()
    model.save('word2vec.model')
    bigram_mod.save('bigram.model')
    trigram_mod.save('trigram.model')
