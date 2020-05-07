from flask import Flask, render_template, request

import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def hello_world():
    return "Hello world!"

    if __name__ == "__main__":
        app.run(host='0.0.0.0')
