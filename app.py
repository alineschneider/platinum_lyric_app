from flask import Flask, render_template, jsonify, request
import plotly
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import json
import nltk
nltk.download('punkt')
nltk.download('stopwords')
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from word_columns import word_columns
import joblib

app = Flask(__name__)

# Set up postgres connection
# app.config["SQLALCHEMY_DATABASE_URI"] = f"postgres://postgres:{password}@platinum-rds.cbu3an3ywyth.us-east-2.rds.amazonaws.com/Platinum_Lyrics"

# Create a Flask-SQLAlchemy instance
# db = SQLAlchemy(app)

# Read csv of word frequencies for successful and unsuccessful song lyrics
word_freq_df = pd.read_csv("https://platinum-lyric-bucket.s3.us-east-2.amazonaws.com/word_freq.csv")

def lyrics_BoW(lyrics):
    # Creating dictionary to match trained ML model, with words as keys and filled with zeros
    model_dict = dict.fromkeys(word_columns, 0)
    
    # Tokenizing user input
    words = nltk.word_tokenize(lyrics)

    # Create an object of class PorterStemmer; set stopwords from NLTK as variable
    porter = PorterStemmer()
    stop_words = stopwords.words('english')

    # Removing stopwords and stemming the remaining ones
    filtered_lyrics = [porter.stem(w) for w in words if not w in stop_words]
    print(f"filtered_lyics from lyrics_BoW: {filtered_lyrics}")

    # Creating frequency of each word and storing in model_dict dictionary
    for word in filtered_lyrics:
        if word in model_dict.keys():
            model_dict[word] += 1
    
    # Creating numpy array from dictionary to feed into ML model
    model_array = np.array([list(model_dict.values())])

    # Load the trained and serialized ML model from file 
    model = joblib.load("NB_model_v3.pkl")

    # Feed model_array into ML Model, returning prediction
    prediction = model.predict(model_array)[0]
    print(f"Prediction from lyrics_BoW: {prediction}")

    if prediction <= 0.5:
        prediction = "False"
    elif prediction > 0.5:
        prediction = "True"
    else:
        prediction = ""

    return prediction

def plot_unique_words_bubble():
    # word_freq_data = word_frequency()
    # word_freq_df = pd.DataFrame(data)
    global word_freq_df

    # Get word frequencies of top 100 successful and unsuccessful songs
    top100_s = word_freq_df.sort_values('freq_successful', ascending=False).iloc[:100]['words'].to_list()
    top100_u = word_freq_df.sort_values('freq_unsuccessful', ascending=False).iloc[:100]['words'].to_list()

    # Get unique words in successful and unsuccessful songs
    top100_s_unique = [word for word in top100_s if word not in top100_u]
    top100_u_unique = [word for word in top100_u if word not in top100_s]

    # Remove the last word for both lists, to censor the last word in top100_u_unique from the visualization
    top100_s_unique = top100_s_unique[:-1]
    top100_u_unique = top100_u_unique[:-1]

    # Get frequencies of unique words
    s_unique_f = []
    for word in top100_s_unique:
        s_unique_f.append(word_freq_df['freq_successful'][word_freq_df['words']==word].values[0])
    u_unique_f = []
    for word in top100_u_unique:
        u_unique_f.append(word_freq_df['freq_unsuccessful'][word_freq_df['words']==word].values[0])
    # Get size list
    s_size = [f*300 for f in s_unique_f]
    u_size = [f*300 for f in u_unique_f]

    # Add lists to dictionary, then to JSON
    unique = {
        'top100_s_unique': top100_s_unique, 's_unique_f': s_unique_f,
        'top100_u_unique': top100_u_unique, 'u_unique_f': u_unique_f,
        's_size': s_size, 'u_size': u_size
    }
    unique_JSON = json.dumps(unique)
    return unique_JSON

def plot_freq_words_bar():
    # word_freq_data = word_frequency()
    # word_freq_df = pd.DataFrame(word_freq_data)
    # word_freq_df = pd.DataFrame(data)
    global word_freq_df

    # Sort df by successful word frequencies
    s_word_freq_df = word_freq_df.sort_values('freq_successful', ascending=False)
    # Get word frequencies of successful and unsuccessful songs
    s_freq = s_word_freq_df.iloc[0:20]['freq_successful'].to_list()
    u_freq = s_word_freq_df.iloc[0:20]['freq_unsuccessful'].to_list()
    words = s_word_freq_df.iloc[0:20]['words'].to_list()
    # Define colors for chart
    colors_s = ['lightsteelblue',] * 20
    colors_s[0] = 'steelblue'
    colors_u = ['darksalmon',] * 20
    colors_u[0] = 'indianred'

    freq = {'words': words,'s_freq': s_freq, 'u_freq': u_freq, 'colors_s': colors_s, 'colors_u': colors_u}
    freq_JSON = json.dumps(freq)
    return freq_JSON

# class WordFreq(db.Model):
#     __tablename__ = 'word_freq'

#     words = db.Column(db.String, primary_key=True)
#     freq_unsuccessful = db.Column(db.Float())
#     freq_successful = db.Column(db.Float())
#     count_unsuccessful = db.Column(db.Float())
#     count_successful = db.Column(db.Float())

#     def __init__(self, words):
#             self.words = words

@app.route("/")
def index():
    # word_freq_data = word_frequency()
    freq_JSON = plot_freq_words_bar()
    unique_JSON = plot_unique_words_bubble()
   
    return render_template(
        "index.html",
        freq_JSON=freq_JSON,
        unique_JSON=unique_JSON
    )

@app.route("/get_lyrics", methods=["GET", "POST"])
def get_lyrics():
    print("Entering /get_lyrics route")
    # Retrieve user input containing lyrics
    lyrics_input = request.args.get('userLyrics', 0, type=str)
    print(f"lyrics_input: {lyrics_input}")
    # Call lyrics_BoW function to process lyrics and run ML model, returning prediction
    prediction = lyrics_BoW(lyrics_input)
    print(f"Prediction from /get_lyrics route: {prediction}")
    return jsonify(result=prediction)
    

# @app.route("/word_freq")
# def word_frequency():
#     # Query database for all values from word_freq table (defined in WordFreq Class)
#     print("Entering word_freq() function.")
#     word_freq = WordFreq.query.all()

#     word_dict = [
#         {
#             "words": word.words,
#             "freq_unsuccessful": word.freq_unsuccessful,
#             "freq_successful": word.freq_successful,
#             "count_unsuccessful": word.count_unsuccessful,
#             "count_successful": word.count_successful

#         } for word in word_freq
#     ]

#     return word_dict



if __name__ == "__main__":
    app.run(debug=False)
    # we first try to grab the port from the app’s environment, and if not found, it defaults to port 5000
    # port = int(os.environ.get('PORT', 5000))
    # app.run(host='0.0.0.0', port=port)
