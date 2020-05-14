# BioReco
DOI search example:
![](demos/doi_1.gif)

Keyword search example:
![](demos/Keyword_1.gif)

---

BioReco is a stand-alone recommender for bioRXiv preprints. It takes user input
either as preprint (**D**)igital (**O**)bject (**I**)dentifier or a series of
keywords as well as the category that user wants to get the suggestions in.

It returns a list of preprints with corresponding information on the title,
version, the final destination (if the preprint is published in a subscription
  journal). User then can visit the preprint or published subscription journal
  article.

## Keywords
  - Web-scraping
  - Collaborative Filtering (cosine similarities)
  - sPacy/SciSpacy
  - Mongo DB
  - Flask
  - Heroku

## Usage
1. Clone the git repository:
`git clone https://github.com/iremnasir/BioReco.git`

2. Install the requirements
`pip install requirements.txt`

3. Import MongoDB dump to a local/cloud Mongo DB server
  Alternatively, use the pseudo code within `Scrape.ipynb` Jupyter notebook and
  customize the dates/ranges as indicated in [bioRXiv api](http://api.biorxiv.org/)

4. Flask/local option run:

`source run_server.sh`

on your CLI.

5. Heroku config is done. All you need to do is to configure your own MongoDB and
create your own app.

## Implementation of a Regressor to predict the citation per year based on article titles

I am also working on a fun side project to develop a model that uses TF-IDF and predicts
the number of citations per year an article may get. This is done under `model_training.ipynb`
and as a preliminary result, seems like `CRISPR`is what brings you citations!


## Improvements to be made

- ~~Add Flask app~~
- ~~Redo pickling on the old scraped categories~~
- Write tests
- Add docstrings and comments throughout the classes.
- ~~Add visualization script~~
- Improve speed
