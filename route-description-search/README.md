## Climbing-specific Word2vec and Doc2vec models

Examples of how to train Word2vec and Dov2vec models on rock-climbing specific corpora. The trained models are included (word2vec.model and doc2vec.model), which can be applied  to climbing-specific text after cleaning (see testing and analysis notebooks for how to use the models).

### Environment and installation instructions

These examples were built and tested using Python 3.9.7, the required packages can be installed in a Conda environment, thus:

```
conda create --name <env_name> --file requirements.yml
```