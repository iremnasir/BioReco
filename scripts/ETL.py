"""Script that extracts entries from Mongo DB, transforms with scispacy
and dumps data and metadata df as pickle"""

import spacy
import pandas as pd
import re
import pymongo
import os

#Load the trained SciSpacy model
ner_bio = spacy.load('en_ner_bionlp13cg_md')

#Mongo DB config
client = pymongo.MongoClient()
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


def ET(query):
    """Takes the category and returns the article-entity df"""
    df = pd.DataFrame()
    print('Fetching the abstracts')
    for i in range(len(query)):
        #Fetch the absract and doi first
        abstract = query[i]['abstract']
        #Remove links
        abstract = re.sub(r'^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$', '', abstract)
        #Tokenize abstract
        tok_abstr = ner_bio(abstract)
        #Build entity-count dictionary
        df1 = pd.DataFrame(ent_count_dict(
                            tok_abstr),index = [i],
                            columns =ent_count_dict(tok_abstr).keys())
        df = pd.concat([df, df1], axis = 0)
        print(f'Row {i} added to the dataframe')
    #Add doi, version and uniqueID
    df['doi'] = get_doi(query)
    df['unique_id'] = get_unique_id(query)
    df['version'] = get_version(query)
    print('NER complete')
    return df

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
        print(f'Element dictionary {i} has been written')
    ind = ele_dict.keys()
    cols_dict = list(ele_dict.values())
    print('Building the dataframe')
    df = pd.DataFrame(data=cols_dict, index=ind)
    df['doi'] = get_doi(query)
    df['version'] = get_version(query)
    df = df.reset_index()

    return df


def load(dataframe, category):
    dataframe.to_pickle(f'../Pickles/{category}.pkl')


def load_meta(dataframe_meta, category):
    dataframe_meta.to_pickle(f'../Pickles/{category}_meta.pkl')


for category in category_list:
    cat_query = query_mongo(category)
    if not os.path.isfile(f'../Pickles/{category}.pkl'):
        df_raw = ET_nested_dict(cat_query)
        load(df_raw, category)
    if not os.path.isfile(f'../Pickles/{category}_meta.pkl'):
        df_meta = get_meta(cat_query)
        load_meta(df_meta, category)
