from flask import Flask, render_template, request
from scripts.models import recommend
from scripts.train import published_pick
import pandas as pd

import warnings
warnings.filterwarnings("ignore")


app = Flask(__name__)

@app.route('/')
@app.route('/index')
def landing():
    return render_template('index.html', title='Landing Page')

@app.route('/input')
def arguments():
    return render_template('input.html')

@app.route('/results')
def recommender():

    user_input = dict(request.args)
    input_values = list(user_input.values())
    user_entry = input_values[0]
    category = input_values[1]
    print(user_entry[0:2])
    if user_entry[0:2] == '10':
        print('Entry is a doi')
        refined_recom = recommend(user_entry, category, keyword=False)
    else:
        print('Entry is a keyword')
        refined_recom = recommend(user_entry, category, keyword=True)
    print(refined_recom)
    return render_template('results.html', tables=[refined_recom.to_html(classes='data')], titles=refined_recom.columns.values)

@app.route('/train')
def train():
    sub_categories = ['biochemistry', 'biophysics', 'cancer biology',
                      'immunology', 'molecular biology']
    for element in sub_categories:
        meta = published_pick(element)
    return render_template('train.html', tables=[meta.to_html(classes='data')], titles=meta.columns.values)





    if __name__ == "__main__":
        app.run(host='0.0.0.0')
