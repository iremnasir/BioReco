"""This module reads the category specific prediction and performs _ models"""

import pandas as pd
from scipy.spatial import distance
import requests
import spacy
from ETL import query_mongo_article, ET, ent_count_dict, entity_dict

#Load the trained SciSpacy model
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
    """Read the user input category and fetch files with duplicates"""
    cat_str = category[:5].lower()
    df = pd.read_pickle(f'../Pickles/{category}.pkl')
    pass


def create_aa_matrix(user_input, df, keyword):
    """Takes the category df and makes and article-article matrix"""
    #Take doi if keyword is False, extract the abstract and model.
    #Create a user df with a single entry
    if keyword == False:
        doi = str(user_input)
        doi_query = query_mongo_article(doi)
        print(doi_query)
        #If there are several versions of the queried article, take the last one
        if len(doi_query) > 1:
            doi_query = [doi_query[-1]]
            print(doi_query)
            df_user = ET(doi_query)
        else:
            df_user = ET(doi_query)
    else:
        user_keyword = str(user_input)
        print(user_keyword)
        user_keyword = re.sub(r'^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$', '', user_keyword)
        tok_kywd = ner_bio(user_keyword)
        print(tok_kywd)
        df_user = pd.DataFrame(ent_count_dict(
                            tok_kywd), index = [9999999],
                            columns =ent_count_dict(tok_kywd).keys())

     #Fill the matrix with zeros for NaN
    df = df.fillna(0)
    #Create a temp df. Unique_ID may be index, change here accordingly
    df_temp = df.drop(['unique_id', 'doi', 'version'], axis=1)
    #Concat it with the user df
    df_temp = pd.concat([df_temp, df_user], axis = 0, ignore_index=False)
    #Create an empty A-A matrix
    AA = np.zeros((len(df_temp), len(df_temp)))
    #Convert into df
    AA = pd.DataFrame(AA, index=df_temp.index, columns=df_temp.index)
    # #Calculate similarities
    u = 9999999
    for v in AA.columns:
        AA.loc[u, v] = 1-distance.correlation(df_temp.loc[u], df_temp.loc[v])
    # usr_article_index = ...
    # upper_suggestion = nr_of_suggestion * 5
    # neighbors = AA.loc[usr_article_index].sort_values(
    #                                 ascending=False)[1:upper_suggestion]
    # #Refine neighbors
    # new_neighbor = []
    # #Filter with overlapping number of entities
    # query_entities = list(df.iloc[usr_article_index][df.iloc[usr_article_index]!=0].index)
    # for i in list(neighbors.index):
    #     neighbor_entities = list(df.iloc[i][df.iloc[i]!=0].index)
    #     intersecting_ent = list(set(query_entities).intersection(neighbor_entities))
    #     if len(intersecting_ent) >= 6:
    #         new_neighbor.append(i)
    # #Collect meta and filter (or not) for different versions
    # df_meta_refined = pd.DataFrame(columns = df_meta.columns)
    # for i in new_neighbor:
    #     recom_article_meta = pd.DataFrame(df_meta.iloc[i]).T
    #     df_meta_refined = pd.concat([df_meta_refined, recom_article_meta], axis = 0)
    # # TODO: Implement if clause for filtering further final publication status
    # # TODO: Implement to filter out same article different version filtering
    #
    #
    # #Pseudo code here:
    # df_doi_refined = df_meta_refined[df_meta_refined['published']!= 'NA']
    # #Where is it published
    # get_doi_publ(df_doi_refined['published'].iloc[0])[1]['message']['short-container-title']
    # #How many times is it published
    # get_doi_publ(df_doi_refined['published'].iloc[0])[1]['message']['is-referenced-by-count']
