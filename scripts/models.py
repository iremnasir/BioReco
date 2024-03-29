"""This module reads the category specific prediction and performs _ models"""

import pandas as pd
from scipy.spatial import distance
import requests
import numpy as np
import re
import os
from scripts.ETL import query_mongo_article, ET, ent_count_dict
import spacy

ner_bio = spacy.load('en_ner_bionlp13cg_md')



def get_doi_publ(doi):
    """
    Adapted from the code in:
    https://github.com/bibcure/doi2bib/blob/master/doi2bib/crossref.py

    Parameters
    ----------
        doi: str
    Returns
    -------
        found: bool
        item: dict
            Response from crossref
    """
    bare_url = "http://api.crossref.org/"
    url = "{}works/{}"
    url = url.format(bare_url, doi)
    r = requests.get(url)
    found = False if r.status_code != 200 else True
    item = r.json()

    return found, item

def read_category_df(category):
    """
    Parameters
    -----------
    Category name that user wants to get suggestions from

    Returns
    ----------
    df: Dataframe of all items in the category, index: articles, columns: entity
    df_meta: Metadata of the articles in the df above
    """

    #Define the path
    PATH = "./Pickles"
    files = os.listdir(PATH)

    #Slice the category to get the unique names out of it
    cat_str = category[1:6]
    meta_file_list = []
    category_file_list=[]
    #Search the file list
    for category in files:
        x = re.search(cat_str, category)
        if x is not None:
            meta = re.search('meta', category)
            if meta is not None:
                meta_file_list.append(category)
            else:
                category_file_list.append(category)
    df = pd.DataFrame()
    for category in category_file_list:
        df1 = pd.read_hdf(f'./Pickles/{category}')
        df = pd.concat([df, df1], axis = 0, ignore_index=True)
    df_meta = pd.DataFrame()
    for category_meta in meta_file_list:
        df1_meta = pd.read_hdf(f'./Pickles/{category_meta}')
        df_meta = pd.concat([df_meta, df1_meta], axis = 0, ignore_index=True)
    return df, df_meta


def recommend(user_input, category, keyword=False):
    """Takes the category df and makes and article-article matrix
    Parameters:
    -----------
    user_input: keyword or doi of the article that user needs suggestions
    category: category dataframe as index:articles & columns: entities

    Returns: A dataframe with suggestions and their metadata
    """

    df, df_meta = read_category_df(category)
    print(df.columns)
    #Take doi if keyword is False, extract the abstract and model.
    #Create a user df with a single entry
    if keyword == False:
        doi = str(user_input)
        doi_query = query_mongo_article(doi)
        #If there are several versions of the queried article, take the last one
        if len(doi_query) > 1:
            doi_query = [doi_query[-1]]
            df_user = ET(doi_query, df)
            df_user['doi'] = doi_query[0]['doi']
            df_user['version'] = doi_query[0]['version']
        else:
            df_user = ET(doi_query, df)
            df_user['doi'] = doi_query[0]['doi']
            df_user['version'] = doi_query[0]['version']
    else:
        user_keyword = str(user_input)
        user_keyword = re.sub(r'^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$', '', user_keyword)
        tok_kywd = ner_bio(user_keyword)
        dummy = np.zeros((1, len(df.columns)))
        df_user = pd.DataFrame(dummy, index =[9999999], columns = df.columns)
        user_dict = ent_count_dict(tok_kywd)
        for key in user_dict.keys():
            df_user[key] = user_dict[key]
    #Fill the matrix with zeros for NaN
    df = df.fillna(0)
    #Create a temp df. Unique_ID may be index, change here accordingly
    try:
        df_temp = df.drop(['unique_id', 'doi', 'version'], axis=1)
        df_user_temp = df_user.drop(['unique_id', 'doi', 'version'], axis=1)

    except KeyError:
        df_temp = df.drop(['index', 'doi', 'version'], axis=1)
        df_user_temp = df_user.drop(['index', 'doi', 'version'], axis=1)

    #Concat it with the user df
    assert len(set(df_temp.columns).intersection((df_user_temp.columns))) >= 1
    df_temp = pd.concat([df_temp, df_user_temp], axis = 0, ignore_index=False)
    df_temp = df_temp.fillna(0)

    #Create an empty Article-Article matrix
    AA = np.zeros((len(df_temp), len(df_temp)))

    #Convert into df
    AA = pd.DataFrame(AA, index=df_temp.index, columns=df_temp.index)

    #Calculate similarities
    #Give a unique index to incoming user
    u = 9999999
    for v in AA.columns:
        AA.loc[u, v] = 1-distance.correlation(df_temp.loc[u], df_temp.loc[v])
    active_user = 9999999
    neighbors = AA.loc[active_user].sort_values(
                                     ascending=False)[1:51]
    neighbors = neighbors.to_frame()

    #Refine neighbors
    #Obtain overlapping number of entities
    query_entities = list(df_user.loc[active_user][df_user.loc[active_user]!=0].index)
    overlapping_count=[]
    for i in list(neighbors.index):
        neighbor_entities = list(df_temp.iloc[i][df_temp.iloc[i]!=0].index)
        intersecting_ent = list(set(query_entities).intersection(neighbor_entities))
        overlapping_count.append(len(intersecting_ent))
    neighbors['overlapping'] = overlapping_count

    #Make a score function as a product of similarity *  # of common entities
    neighbors['score'] = neighbors[9999999]*neighbors['overlapping']

    #Add doi of each
    neighbors['doi'] = df.loc[neighbors.index]['doi']
    neighbors['unique_id'] = df.loc[neighbors.index]['index']

    #Filter with scores higher than 0
    neighbors = neighbors[neighbors['score']> 0]

    #Sort by score
    neighbors = neighbors.sort_values(by=['score'], ascending=False)

    #Drop the same entry if it pops up
    if keyword == False:
        neighbors = neighbors.drop(neighbors[(neighbors.doi == user_input)].index)

    #Drop duplicates, keep first
    neighbors = neighbors.drop_duplicates(keep='first')

    #Collect meta
    meta_refined = neighbors.merge(df_meta, left_on='unique_id', right_on= 'unique_id', how='left')
    meta_refined = meta_refined.sort_values(by=['score'], ascending=False)
    return meta_refined

def listify(dataframe):
    """Function to convert refined dataframe entities into list for displaying
    on the web server

    Parameters:
    ------
    dataframe: Nearest neighbors dataframe

    Returns:
    ------
    A list of columns specified

    """
    column_list = ['score', 'doi_x', 'version', 'title', 'authors',
                       'author_corresponding_institution', 'date', 'published']
    list_of_lists=[]
    for element in column_list:
        list_of_lists.append(dataframe[element].to_list())
    return list_of_lists
