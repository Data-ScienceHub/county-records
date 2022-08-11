import pandas as pd
import pymongo
import json
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd
from bson.json_util import dumps
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

#read in dataset 4, define people, source, event, and roles
df4 = pd.read_csv("1867FluvannaPersonalPropertyTax.csv")
df4['Person A'] = df4['First Name(s)'] + df4['Surname']
df4['Source'] = '1867 Fluvanna Personal Property Tax'
df4['Event'] = df4['Person A'] + ' is paying taxes in the year ' + df4['Year'].apply(str)
df4['Role A'] = 'paid taxes for themselves and their property'
df4['Year'] = df4['Year'].apply(str)


#read in dataset 5, define people, source, event, and roles
df5 = pd.read_csv("1866LouisaRFM.csv")
df5['Person A'] = df5['First Name(s) as written (ex Wm or Wm J)'] + ' ' + df5['Surname']
df5['Source'] = '1866 Louisa RFM'
df5['Event'] = df5['Person A'] + ' is paying taxes in the year ' + df5['Year'].apply(str)
df5['Role A'] = 'paid taxes for themselves and their property'
df5['Year'] = df5['Year'].apply(str)


#turn dataset 1 into json format
df_json_text = df.to_json(orient="records")
df_json = json.loads(df_json_text)

#turn dataset 2 into json format
df_json_text2 = df2.to_json(orient="records")
df_json2 = json.loads(df_json_text2)

#turn dataset 3 into json format
df_json_text3 = df3.to_json(orient="records")
df_json3 = json.loads(df_json_text3)

#turn dataset 4 into json format
df_json_text4 = df4.to_json(orient="records")
df_json4 = json.loads(df_json_text4)

#turn dataset 5 into json format
df_json_text5 = df5.to_json(orient="records")
df_json5 = json.loads(df_json_text5)

myclient = pymongo.MongoClient("mongodb://localhost/")

# this creates a database called story_db
story_db = myclient["story_db"]

# this creates a collection, which is similar to a 'table' in a relational database.
##Need to find way to append new records without deleting full table in order to capture transcribed records##
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

# this creates a collection, which is similar to a 'table' in a relational database.
fluvanna1867_collection = story_db["fluvanna1867_collection"]
fluvanna1867_collection.delete_many({})
fluvanna1867 = fluvanna1867_collection.insert_many(df_json4)

# this creates a collection, which is similar to a 'table' in a relational database.
louisa1866_collection = story_db["louisa1866_collection"]
louisa1866_collection.delete_many({})
louisa1866 = louisa1866_collection.insert_many(df_json5)


# EXPORT EACH OF OUR COLLECTIONS TO JSON FILE FOR ONE SHARED STORY TO POTENTIALLY SHARE WITH OTHER ANCESTRY COMPANIES

cursor = fluvanna_collection.find({})
with open('fluvanna1782_collection.json', 'w') as file:
    json.dump(json.loads(dumps(cursor)), file)

cursor = louis_collection.find({})
with open('louisa1865_collection.json', 'w') as file:
    json.dump(json.loads(dumps(cursor)), file)

cursor = lcbirth_collection.find({})
with open('lcbirth1853_collection.json', 'w') as file:
    json.dump(json.loads(dumps(cursor)), file)
    
cursor = fluvanna1867_collection.find({})
with open('fluvanna1867_collection.json', 'w') as file:
    json.dump(json.loads(dumps(cursor)), file)

cursor = louisa1866_collection.find({})
with open('louisa1866_collection.json', 'w') as file:
    json.dump(json.loads(dumps(cursor)), file)

    
    
@app.route("/", methods=["GET", "POST"])

def transcribe_one():
    '''Post Method allows One Shared Story volunteer to input new records for 
    1782 Fluvanna Property Tax source into MongoDB''' 
    '''Get Method displays transcribe_one.html page, which lists the column headers 
    from 1782 Fluvanna Property Tax source as input fields'''
    if request.method == "POST":
        entry = request.form.to_dict()
        entry['Person A'] = entry['Person Paying Tax First and Middle Name'] + ' ' + entry['Person Paying Tax Surname']
        entry['Person B'] = entry['First Name of Tithe (or taxable person)'] + ' ' + entry['Person Paying Tax Surname']
        entry['Source'] = entry['Fluvanna Archives Collection']
        entry['Event'] = entry['Person A'] + ' paid taxes for property, including potential slaves, cattle, and horses'
        entry['Role A'] = 'paid taxes for property, including potential slaves, cattle, and horses'
        entry['Role B'] = 'paid taxes for property, including potential slaves, cattle, and horses'
        entry['Year'] = '1782'
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

        columns_one_Fluvanna1782 = columns[::3]
        columns_two_Fluvanna1782 = columns[1::3]
        columns_three_Fluvanna1782 = columns[2::3]

        # redirect user to home page
        return render_template('transcribe_one.html', columns=columns, columns_one_Fluvanna1782=columns_one_Fluvanna1782,
                               columns_two_Fluvanna1782=columns_two_Fluvanna1782,
                               columns_three_Fluvanna1782=columns_three_Fluvanna1782)

@app.route("/transcribe_two", methods=["GET", "POST"])
def transcribe_two():
    '''Post Method allows One Shared Story volunteer to input new records for 1865 Louisa Property Tax source into MongoDB''' 
    '''Get Method displays transcribe_two.html page, which lists the column headers from 1865 Louisa Property Tax source as input fields'''
    if request.method == "POST":
        entry = request.form.to_dict()
        entry['Person A'] = entry['Interpreted First Name ET'] + ' ' + entry['Last Name of Residence, Employer, or employment of male negroes']
        entry['Person B'] = entry['First Name'] + ' ' + entry['Last Name']
        entry['Source'] = 'Louisa Property Tax 1865_9 Freedmen Only'
        entry['Event'] = entry['Person A'] + ' paid property tax for ownership of ' + entry['Person B'] + ' in the year ' + entry['Tax Year Blue is North Side Orange is South'] + ' at location ' + entry['Notes on location'] 
        entry['Role A'] = 'paid tax for ownership of ' + entry['Person B']
        entry['Role B'] = 'had tax paid on by ' + entry['Person A']
        entry['Year'] = entry['Tax Year Blue is North Side Orange is South']
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

        columns_one_1865Louisa = columns[::3]
        columns_two_1865Louisa = columns[1::3]
        columns_three_1865Louisa = columns[2::3]

        
        # redirect user to home page
        return render_template('transcribe_two.html', columns=columns, columns_one_1865Louisa=columns_one_1865Louisa, columns_two_1865Louisa=columns_two_1865Louisa, columns_three_1865Louisa=columns_three_1865Louisa)
@app.route("/transcribe_four", methods=["GET", "POST"])
def transcribe_four():
    '''Post Method allows One Shared Story volunteer to input new records for LC Birth source into MongoDB''' 
    '''Get Method displays transcribe_four.html page, which lists the column headers from LC Birth source as input fields'''
    if request.method == "POST":
        entry = request.form.to_dict()
        entry['Person A'] = entry['Child\nFirst Name'] + entry['Child\nLast Name']
        entry['Person B'] = entry['Father/\nOwner\nFirst Name'] + ' ' + entry['Father/\nOwner\nLast Name']
        entry['Person C'] = entry['Mother\nFirst Name'] + ' ' + entry['Mother\nLast Name']
        entry['Source'] = 'Louisa County Birth 1853 Start'
        entry['Event'] = entry['Person A'] + ' was born on ' + entry['DOB\nMONTH'] + ' ' + entry['DOB\nDAY'].apply(str) + ', ' + entry['DOB\nYEAR'].apply(str) + ' to mother ' + entry['Person C'] + ' and father/owner ' + entry['Person B']
        entry['Role A'] = 'born on ' + entry['DOB\nMONTH'] + ' ' + entry['DOB\nDAY'].apply(str) + ', ' + entry['DOB\nYEAR'].apply(str) + ' to mother ' + entry['Person C'] + ' and father/owner ' + entry['Person B']
        entry['Role B'] = 'father/owner of ' + entry['Person A'] + ', born on ' + entry['DOB\nMONTH'] + ' ' + entry['DOB\nDAY'].apply(str) + ', ' + entry['DOB\nYEAR'].apply(str)
        entry['Role C'] = 'gave birth to ' + entry['Person A'] + ' on ' + entry['DOB\nMONTH'] + ' ' + entry['DOB\nDAY'].apply(str) + ', ' + entry['DOB\nYEAR'].apply(str)
        entry['Year'] = entry['DOB\nYEAR'].apply(str)
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

        columns_one_lcbirth = columns[::3]
        columns_two_lcbirth = columns[1::3]
        columns_three_lcbirth = columns[2::3]

        # redirect user to home page
        return render_template('transcribe_four.html', columns=columns, columns_one_lcbirth=columns_one_lcbirth,
                               columns_two_lcbirth=columns_two_lcbirth, columns_three_lcbirth=columns_three_lcbirth)
    
@app.route("/transcribe_five", methods=["GET", "POST"])
def transcribe_five():
    '''Post Method allows One Shared Story volunteer to input new records for LC Birth source into MongoDB''' 
    '''Get Method displays transcribe_five.html page, which lists the column headers from LC Birth source as input fields'''
    if request.method == "POST":
        entry = request.form.to_dict()
        entry['Person A'] = entry['First Name(s)'] + entry['Surname']
        entry['Source'] = '1867 Fluvanna Personal Property Tax'
        entry['Event'] = entry['Person A'] + ' is paying taxes in the year ' + entry['Year'].apply(str)
        entry['Role A'] = 'paid taxes for themselves and their property'
        entry['Year'] = entry['Year'].apply(str)
        
        fluvanna1867 = fluvanna1867_collection.insert_one(entry)
        # redirect user to home page
        return render_template('transcribe_five.html')

    # if get instead of post, send to transcribe.html
    else:
        #read in dataset
        df = pd.read_csv("1867FluvannaPersonalPropertyTax.csv")

        #turn dataset into json format
        df_json_text = df.to_json(orient="records")
        df_json = json.loads(df_json_text)

        keys = df_json[0].keys()

        columns = []

        for key in keys:
            columns.append(key)

        columns_one_1867 = columns[::3]
        columns_two_1867 = columns[1::3]
        columns_three_1867 = columns[2::3]

        # redirect user to home page
        return render_template('transcribe_five.html', columns=columns, columns_one_1867=columns_one_1867,
                               columns_two_1867=columns_two_1867, columns_three_1867=columns_three_1867)    
    
@app.route("/transcribe_six", methods=["GET", "POST"])
def transcribe_six():
    '''Post Method allows One Shared Story volunteer to input new records for LC Birth source into MongoDB''' 
    '''Get Method displays transcribe_five.html page, which lists the column headers from LC Birth source as input fields'''
    if request.method == "POST":
        entry = request.form.to_dict()
        entry['Person A'] = entry['First Name(s) as written (ex Wm or Wm J)'] + ' ' + entry['Surname']
        entry['Source'] = '1866 Louisa RFM'
        entry['Event'] = entry['Person A'] + ' is paying taxes in the year ' + entry['Year'].apply(str)
        entry['Role A'] = 'paid taxes for themselves and their property'
        entry['Year'] = entry['Year'].apply(str)
        
        louisa1866 = louisa1866_collection.insert_one(entry)
        # redirect user to home page
        return render_template('transcribe_six.html')

    # if get instead of post, send to transcribe.html
    else:
        #read in dataset
        df = pd.read_csv("1866LouisaRFM.csv")

        #turn dataset into json format
        df_json_text = df.to_json(orient="records")
        df_json = json.loads(df_json_text)

        keys = df_json[0].keys()

        columns = []

        for key in keys:
            columns.append(key)

        columns_one_1866 = columns[::3]
        columns_two_1866 = columns[1::3]
        columns_three_1866 = columns[2::3]

        # redirect user to home page
        return render_template('transcribe_six.html', columns=columns, columns_one_1866=columns_one_1866,
                               columns_two_1866=columns_two_1866, columns_three_1866=columns_three_1866)    
        
    
@app.route("/search", methods=["GET", "POST"])
def search():
    '''Post Method is not significant right now. No form submit requiring post method'''
    '''Get Method reads in the data from each of our Mongo DB collections, filters out null values, and creates a single row for each individual person, role, and source regardless of whether that person/role is A, B, or C. Ultimately returns a searchable table displaying each person in the MongoDB database'''
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
        
        fluvanna1867_query = fluvanna1867_collection.find(myquery)
        fluvanna1867_query = pd.DataFrame(list(fluvanna1867_query))
        
        louisa1866_query = louisa1866_collection.find(myquery)
        louisa1866_query = pd.DataFrame(list(louisa1866_query))
        
        #fluvanna
        fluvannaA = fluvanna_query.filter(['Person A', 'Role A', 'Source', 'Event', 'Year']
                                          , axis=1).rename(columns = {'Person A':'Name','Role A':'Role'})
        fluvannaA = fluvanna_query.filter(['Person Paying Tax Surname']
                                          , axis=1)
        fluvannaB = fluvanna_query.filter(['Person B', 'Role B', 'Source', 'Event', 'Year']
                                          , axis=1).rename(columns = {'Person B':'Name','Role B':'Role'})
        
        louisaA = louisa_query.filter(['Person A', 'Role A', 'Source', 'Event', 'Year']
                                      , axis=1).rename(columns = {'Person A':'Name','Role A':'Role'})
        louisaB = louisa_query.filter(['Person B', 'Role B', 'Source', 'Event', 'Year']
                                      , axis=1).rename(columns = {'Person B':'Name','Role B':'Role'})
        
        birthA = birth_query.filter(['Person A', 'Role A', 'Source', 'Event', 'Year']
                                    , axis=1).rename(columns = {'Person A':'Name','Role A':'Role'})
        birthB = birth_query.filter(['Person B', 'Role B', 'Source', 'Event', 'Year']
                                    , axis=1).rename(columns = {'Person B':'Name','Role B':'Role'})
        birthC = birth_query.filter(['Person C', 'Role C', 'Source', 'Event', 'Year']
                                    , axis=1).rename(columns = {'Person C':'Name','Role C':'Role'})
        
        fluvanna1867A = fluvanna1867_query.filter(['Person A', 'Role A', 'Source', 'Event', 'Year']
                                                  , axis=1).rename(columns = {'Person A':'Name','Role A':'Role'})
        
        louisa1866A = louisa1866_query.filter(['Person A', 'Role A', 'Source', 'Event', 'Year']
                                              , axis=1).rename(columns = {'Person A':'Name','Role A':'Role'})
        
        people = pd.concat([fluvannaA, fluvannaB, louisaA, louisaB, birthA, birthB, birthC, fluvanna1867A, louisa1866A]).reset_index()
        people = people[people["Name"].str.contains("NaN") == False] 
        people = people[people["Role"].str.contains("None") == False] 
        people = people[people["Name"].str.contains("None") == False]
        people = people[people["Event"].str.contains("None") == False]
        people = people[people["Name"].str.contains("\?") == False]
        return render_template('search.html', people=people)


@app.route("/search_detail", methods=["GET", "POST"])
def search_detail(): 
    if request.method == "POST":
        # redirect user to home page
        return render_template('search_detail.html')

    if request.method == "GET":
        name = request.args.get('name')
        role = request.args.get('role')
        event = request.args.get('event')
        source = request.args.get('source')
        year = request.args.get('year')
        myquery = {"$or" : [{"Person A" : name},{"Person B" : name}]}
        mydoc = fluvanna_collection.find(myquery)
        data = pd.DataFrame(list(mydoc))
        
        myquery2 = {"$or" : [{"Person A" : name},{"Person B" : name}]}
        mydoc2 = louis_collection.find(myquery2)
        data2 = pd.DataFrame(list(mydoc2))
        
        myquery3 = {"$or" : [{"Person A" : name},{"Person B" : name},{"Person C" : name}]}
        mydoc3 = lcbirth_collection.find(myquery3)
        data3 = pd.DataFrame(list(mydoc3)) 
        
        myquery4 = {"Person A" : name}
        mydoc4 = fluvanna1867_collection.find(myquery4)
        data4 = pd.DataFrame(list(mydoc4))
        
        myquery5 = {"Person A" : name}
        mydoc5 = louisa1866_collection.find(myquery5)
        data5 = pd.DataFrame(list(mydoc5))
        
        return render_template('search_detail.html', name=name, role=role, event=event, source=source, year=year, data=data,data2=data2,data3=data3, data4=data4, data5=data5)
