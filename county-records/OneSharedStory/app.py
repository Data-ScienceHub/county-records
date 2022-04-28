import pandas as pd
import pymongo
import json
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd
import numpy as np

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
#@app.after_request
#def after_request(response):
#    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#    response.headers["Expires"] = 0
#    response.headers["Pragma"] = "no-cache"
#    return response

# Custom filter
#app.jinja_env.filters["usd"] = usd

#Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#read in dataset 1, define people, source, event, and roles
df = pd.read_csv("OneSharedStory_1782FluvannaPropertyTax.csv")
df['Person A'] = df['Person Paying Tax First and Middle Name'] + ' ' + df['Person Paying Tax Surname']
df['Person B'] = df['First Name of Tithe (or taxable person)'] + ' ' + df['Person Paying Tax Surname']
df['Source'] = df['Fluvanna Archives Collection']
df['Event'] = np.where(df['Person A']==df['Person B'], df['Person A'] + ' paid taxes for property, including potential slaves, cattle, and horses', df['Person A'] + ' paid tax for ownership of ' + df['Person B'])
df['Role A'] = np.where(df['Person A']==df['Person B'], 'paid taxes for property, including potential slaves, cattle, and horses', 'paid tax for ownership of ' + df['Person B'])
df['Role B'] = np.where(df['Person A']==df['Person B'], 'paid taxes for property, including potential slaves, cattle, and horses', 'had tax paid on by ' + df['Person A'])
df['Year'] = '1782'

#read in dataset 2, define people, source, event, and roles
df2 = pd.read_csv("louisapptax1865_9freedmenonly.csv")
df2['Person A'] = df2['Interpreted First Name ET'] + ' ' + df2['Last Name of Residence, Employer, or employment of male negroes']
df2['Person B'] = df2['First Name'] + ' ' + df2['Last Name']
df2['Source'] = 'Louisa Property Tax 1865_9 Freedmen Only'
df2['Event'] = df2['Person A'] + ' paid property tax for ownership of ' + df2['Person B'] + ' in the year ' + df2['Tax Year Blue is North Side Orange is South'] + ' at location ' + df2['Notes on location'] 
df2['Role A'] = 'paid tax for ownership of ' + df2['Person B']
df2['Role B'] = 'had tax paid on by ' + df2['Person A']
df2['Year'] = df2['Tax Year Blue is North Side Orange is South']

#read in dataset 3, define people, source, event, and roles
df3 = pd.read_csv("LCBirth1853start.csv")
df3['Person A'] = df3['Child\nFirst Name'] + df3['Child\nLast Name']
df3['Person B'] = df3['Father/\nOwner\nFirst Name'] + ' ' + df3['Father/\nOwner\nLast Name']
df3['Person C'] = df3['Mother\nFirst Name'] + ' ' + df3['Mother\nLast Name']
df3['Source'] = 'Louisa County Birth 1853 Start'
df3['Event'] = df3['Person A'] + ' was born on ' + df3['DOB\nMONTH'] + ' ' + df3['DOB\nDAY'].apply(str) + ', ' + df3['DOB\nYEAR'].apply(str) + ' to mother ' + df3['Person C'] + ' and father/owner ' + df3['Person B']
df3['Role A'] = 'born on ' + df3['DOB\nMONTH'] + ' ' + df3['DOB\nDAY'].apply(str) + ', ' + df3['DOB\nYEAR'].apply(str) + ' to mother ' + df3['Person C'] + ' and father/owner ' + df3['Person B']
df3['Role B'] = 'father/owner of ' + df3['Person A'] + ', born on ' + df3['DOB\nMONTH'] + ' ' + df3['DOB\nDAY'].apply(str) + ', ' + df3['DOB\nYEAR'].apply(str)
df3['Role C'] = 'gave birth to ' + df3['Person A'] + ' on ' + df3['DOB\nMONTH'] + ' ' + df3['DOB\nDAY'].apply(str) + ', ' + df3['DOB\nYEAR'].apply(str)
df3['Year'] = df3['DOB\nYEAR'].apply(str)

#turn dataset into json format
df_json_text = df.to_json(orient="records")
df_json = json.loads(df_json_text)

df_json_text2 = df2.to_json(orient="records")
df_json2 = json.loads(df_json_text2)

df_json_text3 = df3.to_json(orient="records")
df_json3 = json.loads(df_json_text3)

myclient = pymongo.MongoClient("mongodb://localhost/")

# this creates a database called story_db
story_db = myclient["story_db"]

# this creates a collection, which is similar to a 'table' in a relational database.
fluvanna_collection = story_db["fluvanna_collection"]
fluvanna_collection.delete_many({})
fluvanna = fluvanna_collection.insert_many(df_json)

# this creates a collection, which is similar to a 'table' in a relational database.
louis_collection = story_db["louis_collection"]
louis_collection.delete_many({})
louis = louis_collection.insert_many(df_json2)

# this creates a collection, which is similar to a 'table' in a relational database.
lcbirth_collection = story_db["lcbirth_collection"]
lcbirth_collection.delete_many({})
lcbirth = lcbirth_collection.insert_many(df_json3)



@app.route("/", methods=["GET", "POST"])

def transcribe_one():
    """complete form for transcription"""
    if request.method == "POST":
        entry = request.form.to_dict()
        fluvanna = fluvanna_collection.insert_one(entry)
        # redirect user to home page
        return render_template('transcribe_one.html')
    # if get instead of post, send to transcribe.html
    else:
        #read in dataset
        df = pd.read_csv("OneSharedStory_1782FluvannaPropertyTax.csv")

        #turn dataset into json format
        df_json_text = df.to_json(orient="records")
        df_json = json.loads(df_json_text)

        keys = df_json[0].keys()

        columns = []

        for key in keys:
            columns.append(key)

        columns_one = columns[::3]
        columns_two = columns[1::3]
        columns_three = columns[2::3]

        header = 'hello world'
        # redirect user to home page
        return render_template('transcribe_one.html', header=header, columns=columns, columns_one=columns_one, columns_two=columns_two, columns_three=columns_three)

@app.route("/transcribe_two", methods=["GET", "POST"])
def transcribe_two():
    """complete form for transcription"""
    if request.method == "POST":
        entry = request.form.to_dict()
        louis = louis_collection.insert_one(entry)
        return render_template('transcribe_two.html')

    # if get instead of post, send to transcribe.html
    else:
        #read in dataset
        df = pd.read_csv("louisapptax1865_9freedmenonly.csv")

        #turn dataset into json format
        df_json_text = df.to_json(orient="records")
        df_json = json.loads(df_json_text)

        keys = df_json[0].keys()

        columns = []

        for key in keys:
            columns.append(key)

        columns_one = columns[::3]
        columns_two = columns[1::3]
        columns_three = columns[2::3]

        
        # redirect user to home page
        return render_template('transcribe_two.html', columns=columns, columns_one=columns_one, columns_two=columns_two, columns_three=columns_three)
@app.route("/transcribe_four", methods=["GET", "POST"])
def transcribe_four():
    """complete form for transcription"""
    if request.method == "POST":
        entry = request.form.to_dict()
        lcbirth = lcbirth_collection.insert_one(entry)
        # redirect user to home page
        return render_template('transcribe_four.html')

    # if get instead of post, send to transcribe.html
    else:
        #read in dataset
        df = pd.read_csv("LCBirth1853start.csv")

        #turn dataset into json format
        df_json_text = df.to_json(orient="records")
        df_json = json.loads(df_json_text)

        keys = df_json[0].keys()

        columns = []

        for key in keys:
            columns.append(key)

        columns_one = columns[::3]
        columns_two = columns[1::3]
        columns_three = columns[2::3]

        # redirect user to home page
        return render_template('transcribe_four.html', columns=columns, columns_one=columns_one, columns_two=columns_two, columns_three=columns_three)
@app.route("/search", methods=["GET", "POST"])
def search():
    """complete form for transcription"""
    if request.method == "POST":
        # redirect user to home page
        return render_template('search.html')

    # if get instead of post, send to transcribe.html
    else:
        myquery = { 'Person A' : {'$ne' : ['null']} }
        fluvanna_query = fluvanna_collection.find(myquery)
        fluvanna_query = pd.DataFrame(list(fluvanna_query))
        louisa_query = louis_collection.find(myquery)
        louisa_query = pd.DataFrame(list(louisa_query))
        birth_query = lcbirth_collection.find(myquery)
        birth_query = pd.DataFrame(list(birth_query))
        #fluvanna
        fluvannaA = fluvanna_query.filter(['Person A', 'Role A', 'Source', 'Event', 'Year'], axis=1).rename(columns = {'Person A':'Name','Role A':'Role'})
        fluvannaB = fluvanna_query.filter(['Person B', 'Role B', 'Source', 'Event', 'Year'], axis=1).rename(columns = {'Person B':'Name','Role B':'Role'})
        louisaA = louisa_query.filter(['Person A', 'Role A', 'Source', 'Event', 'Year'], axis=1).rename(columns = {'Person A':'Name','Role A':'Role'})
        louisaB = louisa_query.filter(['Person B', 'Role B', 'Source', 'Event', 'Year'], axis=1).rename(columns = {'Person B':'Name','Role B':'Role'})
        birthA = birth_query.filter(['Person A', 'Role A', 'Source', 'Event', 'Year'], axis=1).rename(columns = {'Person A':'Name','Role A':'Role'})
        birthB = birth_query.filter(['Person B', 'Role B', 'Source', 'Event', 'Year'], axis=1).rename(columns = {'Person B':'Name','Role B':'Role'})
        birthC = birth_query.filter(['Person C', 'Role C', 'Source', 'Event', 'Year'], axis=1).rename(columns = {'Person C':'Name','Role C':'Role'})
        people = pd.concat([fluvannaA, fluvannaB, louisaA, louisaB, birthA, birthB, birthC]).reset_index()
        people = people[people["Name"].str.contains("NaN") == False] 
        people = people[people["Role"].str.contains("None") == False] 
        people = people[people["Name"].str.contains("None") == False]
        people = people[people["Event"].str.contains("None") == False]
        people = people[people["Name"].str.contains("\?") == False]
        return render_template('search.html', people=people)
    



