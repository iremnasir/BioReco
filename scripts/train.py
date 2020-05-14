from scripts.ETL import ner_bio
from scripts.models import get_doi_publ
import pymongo
import pandas as pd
import os
import re

#Mongo DB config
client = pymongo.MongoClient()
#client = pymongo.MongoClient("mongodb+srv://irem:iremnasir@cluster0-hzvy2.mongodb.net/BioReco?retryWrites=true&w=majority")
db = client.BioReco

def read_category_meta_df(category):
    """
    Parameters
    -----------
    Category name that user wants to get suggestions from

    Returns
    ----------
    df_meta: Metadata of the articles in the df above
    """

    #Define the path
    PATH = "./Pickles"
    files = os.listdir(PATH)

    #Slice the category to get the unique names out of it
    cat_str = category[1:6]
    meta_file_list = []
    #Search the file list
    for category in files:
        x = re.search(cat_str, category)
        if x is not None:
            meta = re.search('meta', category)
            if meta is not None:
                meta_file_list.append(category)
    df_meta = pd.DataFrame()
    for category_meta in meta_file_list:
        df1 = pd.read_hdf(f'./Pickles/{category_meta}')
        df_meta = pd.concat([df_meta, df1], axis = 0, ignore_index=True)
    return df_meta


def published_pick(category):
    df_meta = read_category_meta_df(category)
    df_meta = df_meta[df_meta['published']!='NA']
    meta_short = df_meta[['title', 'published', 'date', 'author_corresponding_institution']]
    query = meta_short['published'].apply(get_doi_publ)
    journal_name = []
    citation_count = []
    for paper in query:
        journal_name.append(paper[1]['message']['short-container-title'])
        citation_count.append(paper[1]['message']['is-referenced-by-count'])
    meta_short['journal'] = journal_name
    meta_short['citation_count'] = citation_count
    meta_short.to_csv(f'./{category}_meta_short.csv')
    return meta_short
