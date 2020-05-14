"""Script that extracts entries from Mongo DB, transforms with scispacy
and dumps data and metadata df as pickle"""

import spacy
import pandas as pd
import re
import pymongo
import os
import numpy as np


#Load the trained SciSpacy model
ner_bio = spacy.load('en_ner_bionlp13cg_md')

#Mongo DB config
client = pymongo.MongoClient()
#client = pymongo.MongoClient
#("mongodb+srv://irem:iremnasir@cluster0-hzvy2.mongodb.net/BioReco?retryWrites=true&w=majority")
db = client.BioReco
category_list = db.BioReco_raw.distinct("category")
category_list.remove('')

def entity_dict(tokenized_abst):
    """Build a dictionary of k:entity and v:ent_tag"""
    tok_dict = {}
    for ent in tokenized_abst.ents:
        tok_dict[f'{ent.text}'] = ent.label_
    return tok_dict

def ent_count_dict(tokenized_abst):
    """Returns an entity count dictionary from tokenized abstract"""
    ent_list = []
    for ent in tokenized_abst.ents:
        ent_list.append(ent)
    #Convert them to string
    ent_list = [str(i) for i in ent_list]
    #Build an entity dictionary with labels
    ent_dict = entity_dict(tokenized_abst)
    #Get the keys to loop the entity list for counts
    ent_keys = ent_dict.keys()
    #Make a new dictionary of (k:ent, v: count)
    ent_app = {}
    for element in ent_keys:
        ent_app[element] = ent_list.count(element)
    return ent_app

def get_doi(query):
    """Make the doi list from the query"""
    doi_list = []
    for i in range(len(query)):
        doi_list.append(query[i]['doi'])
    return doi_list

def get_unique_id(query):
    """Make the Mongo UniqueID list from the query"""
    unique_id = []
    for i in range(len(query)):
        unique_id.append(query[i]['_id'])
    return unique_id

def get_version(query):
    """Make the version list from the query"""
    ver_list = []
    for i in range(len(query)):
        ver_list.append(query[i]['version'])
    return ver_list

def query_mongo(category):
    """Query Mongo DB with a specific category"""
    query_cat = list(db.BioReco_raw.find({'category': f'{category}'}))
    size = len(query_cat)
    print(f'There are {size} articles in {category} category')
    return query_cat

def get_meta(query):
    """Makes a metadata df"""
    df_meta = pd.DataFrame()
    cat_list = ['version', 'doi', 'title', 'authors',
                'author_corresponding', 'author_corresponding_institution',
                'date', 'version', 'type', 'category', 'published', 'server']
    for meta in cat_list:
        meta_list = []
        for i in range(len(query)):
            meta_list.append(query[i][meta])
        df_meta[meta] = meta_list
    df_meta['unique_id'] = get_unique_id(query)
    print('Metadata Recoded')
    return df_meta

def query_mongo_article(doi):
    """Query Mongo DB with a specific doi"""
    query_cat = list(db.BioReco_raw.find({'doi': f'{doi}'}))
    size = len(query_cat)
    print(f'There are {size} articles in {doi} category')
    return query_cat


def ET_nested_dict(query):
    ele_dict = {}
    #Fetch the absract and doi first
    for i in range(len(query)):
        abstract = query[i]['abstract']
        #Remove links
        abstract = re.sub(r'^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$', '', abstract)
        #Tokenize abstract
        tok_abstr = ner_bio(abstract)
        ele_dict[query[i]['_id']] = ent_count_dict(tok_abstr)
    ind = ele_dict.keys()
    cols_dict = list(ele_dict.values())
    print('Building the dataframe')
    df = pd.DataFrame(data=cols_dict, index=ind)
    df['doi'] = get_doi(query)
    df['version'] = get_version(query)
    df = df.reset_index()
    return df

def ET(query, category_df):
    """Takes the category and returns the article-entity df"""
    dummy = np.zeros((1, len(category_df.columns)))
    df = pd.DataFrame(dummy, index =[9999999], columns = category_df.columns)
    #Fetch the absract and doi first
    abstract = query[0]['abstract']
    #Remove links
    abstract = re.sub(r'^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$', '', abstract)
    #Tokenize abstract
    tok_abstr = ner_bio(abstract)
    #Build entity-count dictionary
    user_dict = ent_count_dict(tok_abstr)
    for key in user_dict.keys():
        df[key] = user_dict[key]
    return df


def load(dataframe, category):
    dataframe.to_hdf(f'../Pickles/{category}.h5', key='df', format='fixed')


def load_meta(dataframe_meta, category):
    dataframe_meta.to_hdf(f'../Pickles/{category}_meta.h5', key='df_meta', format='fixed')

#For scraping purposes
# sub_categ = ['biophysics', 'bioinformatics', 'evolutionary biology', 'scientific communication and education']
# for category in sub_categ:
#     cat_query = query_mongo(category)
#     df_raw = ET_nested_dict(cat_query)
#     load(df_raw, category)
#     df_meta = get_meta(cat_query)
#     load_meta(df_meta, category)

# for category in category_list:
#     cat_query = query_mongo(category)
#     if not os.path.isfile(f'../Pickles/{category}.h5'):
#         df_raw = ET_nested_dict(cat_query)
#         load(df_raw, category)
#     if not os.path.isfile(f'../Pickles/{category}_meta.h5'):
#         df_meta = get_meta(cat_query)
#         load_meta(df_meta, category)
