from app import app, lm
from flask import request, redirect, render_template, url_for, flash, session, Response, send_file
from flask.ext.login import login_user, logout_user, login_required, current_user
from .forms import LoginForm
from .user import User
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from pymongo.errors import DuplicateKeyError
import json
import random
import csv
import smtplib
from flask import g
from .auth import OAuthSignIn
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText



@app.route('/')
def home():
    return render_template('base.html')


@app.route('/home2')
def home2():
    return render_template('base.html')

@app.route('/iiitd')
def iiitd():
    return redirect("http://www.iiitd.ac.in")
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        if form.username.data=="admin@flickscore":
            user = app.config['USERS_COLLECTION'].find_one({"_id": form.username.data})
            if user and User.validate_login(user['password'], form.password.data):
                user_obj = User(user['_id'])
                login_user(user_obj)
                session['username'] = form.username.data
                flash("Logged in successfully!", category='success')
                return redirect(url_for("admin"))
        
        else:
            user = app.config['USERS_COLLECTION'].find_one({"_id": form.username.data})
            print user
            if user and user['password'] == form.password.data:
                user_obj = User(user['_id'])
                login_user(user_obj)
                session['username'] = form.username.data
                print session['username']
                flash("Logged in successfully!", category='success')
                return redirect(request.args.get("next") or url_for("write"))
    return render_template('login.html', title='login', form=form)

@app.route('/register' , methods=['GET','POST'])
def register():
    er = "not set"
    if request.method == 'GET':
        return render_template('register.html')
    #user = User(request.form['username'] , request.form['password'],request.form['email'])
    collection = MongoClient()["imdb"]["users"]
    ratings = MongoClient()["imdb"]["ratings"]
    
    user = request.form['username']
    password = request.form['password']
    email = request.form['email']
    dd = request.form['dob-day']
    mm = request.form['dob-month']
    yy = request.form['dob-year']
    gender = request.form['gender']
    state = request.form['state']
    lang =  request.form.getlist('lang')
    job = request.form['job']
    dob = ""
    dob += dd + "-" + mm + "-" + yy 
    pass_hash = generate_password_hash(password, method='pbkdf2:sha256')
    connection = MongoClient()
    db=connection.imdb
    userData = db.users.find()
    email_list=[]
    for row in userData:
        email_list.append(row['email'])
    if email in email_list:
        er = "Email already registered"
        return render_template('register.html', name = er)
    
    try:
        collection.insert({"_id": user, "password": password, "email": email, "dob": dob, "gender": gender, "state": state, "languages": lang, "job": job})
        print "User created."
        flash('User successfully registered')
        return redirect(url_for('login'))
    except DuplicateKeyError:
        print "User already present in DB."
        flash("This username exists!", category='error')
        er = "username taken"
        return render_template('register.html', name = er)


@app.route('/logout')
def logout():
    logout_user()
    return render_template('base.html')
    #return redirect(url_for('login'))

@app.route('/admin' , methods=['GET','POST'])
@login_required
def admin():
    return render_template('admin.html')

@app.route('/recoveryForm',methods=['GET', 'POST'])
def recoveryForm():
    return render_template('recovery.html')

@app.route('/recoverPass',methods=['GET', 'POST'])
def recoverPass():
    connection = MongoClient()
    db=connection.imdb
    user = request.form['username']

    rec = db.users.find({"_id":user})
    for row in rec:
        print row

        email_id=row['email']
        password = row['password']
    
    
 
    fromaddr = "flickscore.iiitd@gmail.com"
    toaddr = email_id
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Password"
 
    body = "" + str(password)
    msg.attach(MIMEText(body, 'plain'))
 
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "change##1")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

    return render_template('base.html')

@app.route('/review',methods=['GET', 'POST'])
@login_required
def review():
    connection = MongoClient()
    db=connection.imdb
    #[u'Hindi', u'Telugu']
    uname = session['username']
    item = db.users.find({"_id": uname},{"languages": 1}) 
    #uDict = json.load(item)
    print "We got these langs!!!!"
    for record in item:
        string = record['languages']
    print type(string)
    lis = []
    ranList=[]
    for l in string:
        l.strip("u")
        lis.append(db.movies.find( { "language":l }))
    for i in range(0,len(lis)):
        if lis[i].count()<20:
            ranList.append([k for k in range(0,lis[i].count())])
        else:
            ranList.append(list(random.sample(range(0, lis[i].count()), 20)))
    print type(ranList)
    print ranList
    return render_template('review_20.html',my_list = lis, rList = ranList)
    

@app.route('/rating',methods=['GET', 'POST'])
@login_required
def rating():
    connection = MongoClient()
    db=connection.imdb
    #collection = MongoClient()["imdb"]["users"]
    #ratings = MongoClient()["imdb"]["ratings"]
    if request.method == "POST":
        if request.form['submit'] == 'submitmore':        
            result = request.form   
            qstr = "{"                 #dictionary
            for key in result.keys():
                for value in result.getlist(key):
                    if key != "submit":

                        qstr += "\"" + "rated."+ key + "\"" + " : " + value + ","
            qstr = qstr[0:-1]
            qstr += "}"
            

            uname = session['username']
            if db.ratings.find({"_id": uname}).count() > 0:
                print "user exists"
                item = db.ratings.find({"_id": uname},{"rated": 1}) 
                for record in item:
                    string = record['rated']
                res=string.copy()
                res.update(result)
                
                db.ratings.update(
                { "_id":uname },
                {
                    "_id":uname,
                    "rated": res
                })
                
                
            else:
                print "no ratings yet" 
                #jsonstr = json.dump(result)
                db.ratings.insert({"_id": uname, "rated": result})
                print "inserted one row"

            flash("Rated movies successfully!", category='success')

            #############################################
            connection = MongoClient()
    
            uname = session['username']
            item = db.users.find({"_id": uname},{"languages": 1}) 
            #uDict = json.load(item)
            print "We got these langs!!!!"
            for record in item:
                string = record['languages']
            
            lis = []
            ranList=[]
            ratedMovie = {}
            for l in string:
                l.strip("u")
                lis.append(db.movies.find( { "language":l }))

            ratedMovie = db.ratings.find_one({"_id": uname})
            #print ratedMovie
            for i in range(0, len(lis)):
                for j in range(0,lis[i].count()):
                    #print lis[i][j]['movie_id'],ratedMovie.get(lis[i][j]['movie_id'])
                    if 'u\''+ lis[i][j]['movie_id'] in ratedMovie:
                        del lis[i][j]
                        print "inside pop loop"
                        print lis[i][j]['movie_id']



            #print lis[0][1]['movie_id']
            for i in range(0,len(lis)):
                if lis[i].count()<20:
                    ranList.append([k for k in range(0,lis[i].count())])
                else:
                    ranList.append(list(random.sample(range(0, lis[i].count()), 20)))
    
    
            return render_template("review.html",my_list = lis, rList = ranList)

        else:
            result = request.form   
            qstr = "{"                 #dictionary
            for key in result.keys():
                for value in result.getlist(key):
                    if key != "submit":

                        qstr += "\"" + "rated."+ key + "\"" + " : " + value + ","
            qstr = qstr[0:-1]
            qstr += "}"
            print qstr
            #qjson = json.dumps(json.loads(qstr))
            #ast.literal_eval(json.dumps(r))
            #print qjson

            uname = session['username']
            if db.ratings.find({"_id": uname}).count() > 0:
                print "user exists"
                
                item = db.ratings.find({"_id": uname},{"rated": 1}) 
                for record in item:
                    string = record['rated']
                res=string.copy()
                res.update(result)
                
                db.ratings.update(
                { "_id":uname },
                {
                    "_id":uname,
                    "rated": res
                })
                
            else:
                print "no ratings yet" 
                #jsonstr = json.dump(result)
                db.ratings.insert({"_id": uname, "rated": result})
                print "inserted one row"

            flash("Rated movies successfully!", category='success')

            item = db.users.find({"_id": uname},{"languages": 1}) 
            for record in item:
                string = record['languages']
            
            lis = []
            for l in string:
                l.strip("u")
                lis.append(db.recmovies.find( { "language":l }))
                
            return render_template("recmovies.html",my_list = lis)

            

    return render_template('base.html')


@app.route('/ratingmore',methods=['GET', 'POST'])
@login_required
def ratingmore():
    connection = MongoClient()
    db=connection.imdb
    #collection = MongoClient()["imdb"]["users"]
    #ratings = MongoClient()["imdb"]["ratings"]
    if request.method == "POST":
        if request.form['submit'] == 'submit':        
            result = request.form   
            qstr = "{"                 #dictionary
            for key in result.keys():
                for value in result.getlist(key):
                    if key != "submit":

                        qstr += "\"" + "rated."+ key + "\"" + " : " + value + ","
            qstr = qstr[0:-1]
            qstr += "}"
            print qstr

            uname = session['username']
            if db.ratings.find({"_id": uname}).count() > 0:
                print "user exists"
                item = db.ratings.find({"_id": uname},{"rated": 1}) 
                for record in item:
                    string = record['rated']
                res=string.copy()
                res.update(result)
                
                db.ratings.update(
                { "_id":uname },
                {
                    "_id":uname,
                    "rated": res
                })
                
            else:
                print "no ratings yet" 
                #jsonstr = json.dump(result)
                db.ratings.insert({"_id": uname, "rated": result})
                print "inserted one row"

            flash("Rated movies successfully!", category='success')
    
            uname = session['username']
            item = db.users.find({"_id": uname},{"languages": 1}) 
            for record in item:
                string = record['languages']
            
            lis = []
            for l in string:
                l.strip("u")
                lis.append(db.recmovies.find( { "language":l }))
    
    
            return render_template("recmovies.html",my_list = lis)




@app.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    return render_template('base.html')

@app.route('/showMovie', methods=['GET', 'POST'])
@login_required
def showMovie():
    return render_template('review.html')


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return render_template('settings.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template('contact.html')

@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')

@app.route('/dataset', methods=['GET', 'POST'])
def dataset():
    connection = MongoClient()
    db=connection.imdb
    if request.method == "POST":
        if request.form['submit'] == 'submit': 
            data=db.ratings.find()
            dataList = []
            #dataset=open('ratings_data.csv','wb')
            #wr=csv.writer(dataset,delimiter=',')
            for user in data:
                lis=user['rated']
                for key in lis.iterkeys():
                    if key!='submit':
                        
                        dataList.append([user['_id'],key,int(lis[key][0])])
            return render_template('viewdata.html', result = dataList)
            #dataset.close()
            #cs = '1,2,3\n4,5,6\n'
            '''return send_file('../ratings_data.csv',
                     mimetype='text/csv',
                     attachment_filename='ratings_data.csv',
                     as_attachment=True)'''

    return render_template('base.html')


@lm.user_loader
def load_user(username):
    u = app.config['USERS_COLLECTION'].find_one({"_id": username})
    if not u:
        return None
    return User(u['_id'])
