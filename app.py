import os
import base64
import cv2
from datetime import *
from flask import *
import json
from model.FER import FacialExpressionModel
from flask_cors import CORS
from werkzeug.utils import secure_filename
import psycopg2
import uuid
from camera import stop3, gen, validProfile, stop1
from db import conn
from passlib.hash import bcrypt
from flask_session import Session
from model.recommendation.recommend import recommend

app = Flask(__name__)
app.cnn = FacialExpressionModel()
CORS(app)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.config['SECRET_KEY'] = 'df0331cefc6c2b9a5d0208a726a5d1c0fd37324feba25506'
app.config['UPLOAD_FOLDER']= os.path.join(app.root_path, "static\images\profile")
app.rec = recommend(app.root_path)

def isLogin():
    if not session.get("user"):
        return True
    else: False


@app.route("/history")
def history():

    cur = conn.cursor()
    cur.execute("select mood, after_mood, activity, category, m.mood_id, date, image, after_image from mood m join recommendation r on m.mood_id = r.mood_id where m.user_id=%s order by m.mood_id desc"% (session["user"]))
    res = cur.fetchall()
    mood = []
    c={"bmood":res[0][0], "amood":res[0][1], "activity":{}, "date":res[0][5].strftime('%Y-%m-%d %H:%M:%S'), "bimg":res[0][6], "aimg":res[0][7]}
    m = res[0][4]
    for i in res:
        if m!=i[4]:
            c["activities"] = list(c["activity"].items())
            mood.append(c)
            c={"bmood":i[0], "amood":i[1], "activity":{}, "date":i[5].strftime('%Y-%m-%d %H:%M:%S'), "bimg":i[6], "aimg":i[7]}
            m= i[4]
        if i[3]=="Songs":
            if "Songs" in c["activity"].keys():
                c["activity"][i[3]].append(i[2])
            else:
                c["activity"][i[3]] = [i[2]]
        else:
            c["activity"][i[3]] = i[2]
    c["activities"] = list(c["activity"].items())
    mood.append(c)

    cur.execute("select email, name, password, birth_date, profile from users where user_id=%s"% (session["user"]))
    res = cur.fetchall()
    user = {"email":res[0][0], "name":res[0][1], "password":res[0][2], "date":res[0][3], "img":res[0][4]}
    conn.commit()
    cur.close()
    return render_template('history.html', history=mood, user=user, login=isLogin())


@app.route("/editprofile",  methods=['POST'])
def editprofile():
    if request.method=="POST":
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        date = request.form['date']
        file = request.files["file"]
        print(file.filename)
        hashed = None
        fname = None
        if  password:
            hashed = bcrypt.hash(password)
        elif file:
            fname = str(uuid.uuid1()) + '.' + file.filename.split('.')[-1]
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            if not validProfile(os.path.join(app.config['UPLOAD_FOLDER'], fname)):
                flash('Profile image is not valid')
        
        date = date.split('-')
        birth_date = psycopg2.Date(int(date[0]), int(date[1]), int(date[2]))
        query = "update users set email='"+email+"', birth_date="+str(birth_date)+", name='"+name+"'"
        if hashed:
            query+= ", password='"+hashed+"'"
        if fname:
            query+= ", profile='"+fname+"'"
        query+=" where user_id="+str(session["user"])+" returning user_id"
        cur = conn.cursor()
        cur.execute(query)
        user = cur.fetchall()
        conn.commit()
        cur.close()
        return redirect(url_for("history")) 
    return redirect(url_for("history"))


@app.route("/recommende")
def recommende():
    return render_template('analyze_dashboard.html')

@app.route("/liked_activity/<id>")
def liked_activity(id):
    cur = conn.cursor()
    cur.execute("update recommendation set liked = not liked where recommend_id=%s returning mood_id" % (id))
    res = cur.fetchall()
    conn.commit()
    cur.close()
    return redirect(url_for("recommend", id=res[0][0]))

@app.route("/complete_activity/<id>")
def complete_activity(id):
    cur = conn.cursor()
    cur.execute("update recommendation set completed = not completed where recommend_id=%s returning mood_id" % (id))
    res = cur.fetchall()
    mood = res[0][0]
    cur.execute("select recommend_id from recommendation where completed=false and mood_id=%s" % (mood))
    res = cur.fetchall()   
    conn.commit()
    cur.close()
    if len(res)>0:
        return redirect(url_for("recommend",id=mood))
    else:
        return redirect(url_for("reanalyze", id=mood))

@app.route("/analyze")
def analyze():
    if session.get('user'):
        cur = conn.cursor()
        cur.execute("select mood_id, activity from recommendation where completed=false and mood_id=(select mood_id from mood where user_id=%s order by date desc limit 1)" % (session['user']))
        res = cur.fetchall()        
        conn.commit()
        if len(res)>0:
            cur.close()
            return redirect(url_for("recommend", id=res[0][0]))
        else:
            cur.execute("select mood_id from mood where mood_id=(select mood_id from mood where user_id=%s order by date desc limit 1) and after_mood is null" % (session['user']))
            res = cur.fetchall()       
            conn.commit()
            cur.close()
            if len(res)>0:
                return redirect(url_for("reanalyze", id=res[0][0]))

    return render_template('analyze_face.html', detect=False, login=isLogin())

@app.route("/reanalyze/<int:id>")
def reanalyze(id):
    return render_template('analyze_face.html', detect=False, login=isLogin(), reana=True, mood_id = id)


@app.route("/unknown_recommend/<mood>/<img>")
def unknown_recommend(mood,img):
    ret ={}
    
    fun = json.loads(app.rec.other_recommend([mood],"Fun", [], None))
    ret["Fun"] = fun
    sport = json.loads(app.rec.other_recommend([mood],"Sport",[], None))
    ret["Sport"] = sport
    book = json.loads(app.rec.book_recommend(mood, [], None, [])) 
    ret["Book"] = book
    movie = json.loads(app.rec.movie_recommend(mood, [], None, []))
    ret["Movie"] = movie 
    songs = json.loads(app.rec.song_recommend(mood, []))
    ret["Songs"] = songs 

    name = "Anonymous"
    age =  "--"
    return render_template('analyze_dashboard.html', mood = mood, img=img, name = name, age=age,login=isLogin(), now= datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ret=ret)
    

@app.route("/recommend/<int:id>")
def recommend(id):
    if not session.get('user'):
        return redirect(url_for('login'))
        

    cur = conn.cursor()
    cur.execute("select category,activity,completed, mood, recommend_id, liked, image, date from mood m join recommendation r on m.mood_id = r.mood_id where m.mood_id=%s" % (id))
    res = cur.fetchall()
    if len(res)>0:
        rec={"Movie":[],"Fun":[],"Sport":[],"Songs":[],"Book":[]}
        for i in res:
            rec[i[0]].append(i[1])
        ret={}
        ret["Movie"] = json.loads(app.rec.get_movie(rec["Movie"]))
        ret["Sport"] = json.loads(app.rec.get_sport(rec["Sport"]))
        ret["Fun"] = json.loads(app.rec.get_fun(rec["Fun"]))
        ret["Songs"] = json.loads(app.rec.get_song(rec["Songs"]))
        ret["Book"] = json.loads(app.rec.get_book(rec["Book"]))
        for i in res:
            for j in ret[i[0]]:
                if i[0]=="Songs" and j["name"]==i[1]:
                    j["id"] = i[4]
                    j["like"] = i[5]
                    j["completed"] = i[2]
                    break
                elif i[0]=="Fun" and j["Title"]==i[1]:
                    j["id"] = i[4]
                    j["like"] = i[5]
                    j["completed"] = i[2]
                    break
                elif i[0]=="Sport" and j["Title"]==i[1]:
                    j["id"] = i[4]
                    j["like"] = i[5]
                    j["completed"] = i[2]
                    break
                elif i[0] =="Book" and j["title"]==i[1]:
                    j["id"] = i[4]
                    j["like"] = i[5]
                    j["completed"] = i[2]
                    break
                elif i[0] =="Movie" and j["title"]==i[1]:
                    j["id"] = i[4]
                    j["like"] = i[5]
                    j["completed"] = i[2]
                    break        
        mood,img, date=res[0][3],res[0][6],res[0][7]
        cur.execute("select name, birth_date from users where user_id=%s" % (session['user']))
        res = cur.fetchall()
        today = date.today()
        born = res[0][1]
        conn.commit()
        cur.close()
        age =  today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return render_template('analyze_dashboard.html', mood = mood, img=img, name = res[0][0], age=age,login=isLogin(), now= date.strftime('%Y-%m-%d %H:%M:%S'), ret=ret)


    

    cur.execute("select mood,image from mood where mood_id=%s" % (id))
    res = cur.fetchall()
    mood,img = res[0]
    conn.commit()

    cur.execute("select name, birth_date, fun,sport,book,movie,songs, genre_pref from users where user_id=%s" % (session['user']))
    res = cur.fetchall()
    name,born = res[0][0], res[0][1]
    pref=res[0][7]
    pref = pref.split(',')
    rec=[]
    fun=None
    cur.execute("select category,activity,liked from mood m join recommendation r on m.mood_id = r.mood_id where user_id=%s order by recommend_id desc" % (session['user']))
    data = cur.fetchall()
    d = {"Movie": {"like":None, "done":[]}, "Book": {"like":None, "done":[]}, "Songs": {"like":None, "done":[]},"Fun": {"like":None, "done":[]},"Sport": {"like":None, "done":[]}}
    for i in data:
        if i[2] and d[i[0]]["like"]==None:
            d[i[0]]["like"] = i[1]
        else: 
            d[i[0]]["done"].append(i[1])

    print(d)
    ret ={}
    if res[0][2]:
        fun = json.loads(app.rec.other_recommend([mood],"Fun", d["Fun"]["done"], d["Fun"]["like"]))
        print(fun)
        rec.append([id, "Fun", fun[0]["Title"]])
        ret["Fun"] = fun
    sport=None
    if res[0][3]:
        sport = json.loads(app.rec.other_recommend([mood],"Sport", d["Sport"]["done"], d["Sport"]["like"]))
        rec.append([id, "Sport", sport[0]["Title"]]) 
        ret["Sport"] = sport
    book=None
    if res[0][4]:
        book = json.loads(app.rec.book_recommend(mood, d["Book"]["done"], d["Book"]["like"], pref))
        rec.append([id, "Book", book[0]["title"]]) 
        ret["Book"] = book
    movie=None
    if res[0][5]:
        movie = json.loads(app.rec.movie_recommend(mood, d["Movie"]["done"], d["Movie"]["like"], pref))
        rec.append([id, "Movie", movie[0]["title"]])
        ret["Movie"] = movie 
    songs=None
    if res[0][6]:
        songs = json.loads(app.rec.song_recommend(mood, d["Songs"]["done"]))
        for i in songs:
            rec.append([id, "Songs", i["name"]])
        ret["Songs"] = songs 
    
    ins = ','.join(cur.mogrify("(%s,%s,%s)", i).decode('utf-8') for i in rec)
    print(ins)
    cur.execute("insert into recommendation (mood_id, category, activity) values"+ (ins) + "returning recommend_id, category")
    res = cur.fetchall()
    conn.commit()
    for i in res:
        for j in ret[i[1]]:
            if "id" in j:
                j["id"] = i[0]
                j["like"] = False
                j["completed"] = False
                break
    today = datetime.today()
    conn.commit()
    cur.close()
    age =  today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return render_template('analyze_dashboard.html', mood = mood, img=img, name = name, age=age,login=isLogin(), now= datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ret=ret)
    
@app.route('/video_feed')
def video_feed():
    return Response(gen(app.cnn), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/capture")
def capture():
    mood_id = None
    if session.get('user'):
        img,face = stop3(app.cnn, session.get('profile'), app.config['UPLOAD_FOLDER'], app.root_path)
        if len(face)>0:
            cur = conn.cursor()
            cur.execute("insert into mood (mood, image, date, user_id) values('%s','%s','%s',%s) returning mood_id" % (face[0],img,datetime.now(),session['user']))
            res = cur.fetchall()
            mood_id = res[0][0]
            conn.commit()
            cur.close()    
    else:
        img, face= stop1(app.cnn, app.root_path)
    mood =""
    if len(face)==1: 
        mood= face[0]

    if len(face)==0:
        valid=True
    else: 
        valid = False
    return render_template('analyze_face.html', face = face, mood=mood, img=img, valid=valid, login=isLogin(), mood_id=mood_id)

@app.route("/recapture/<int:id>")
def recapture(id):
    mood_id = None
    img,face = stop3(app.cnn, session.get('profile'), app.config['UPLOAD_FOLDER'], app.root_path)
    if len(face)>0:
        cur = conn.cursor()
        cur.execute("update mood set after_mood='%s', after_image='%s', after_date='%s' where mood_id=%s" % (face[0],img,datetime.now(),id))
        conn.commit()
        cur.close()    
    mood =""
    if len(face)==1: 
        mood= face[0]

    if len(face)==0:
        valid=True
    else: 
        valid = False
    return render_template('analyze_face.html', face = face, mood=mood, img=img, valid=valid, login=isLogin(), reana=True, mood_id=id)

@app.route('/again__detect')
def again__detect():
    return render_template('analyze_face.html', feed=True, login=isLogin())

@app.route('/again_detect/<int:id>')
def again_detect(id):
    cur = conn.cursor()
    cur.execute("delete from mood where mood_id=%s" % (id))      
    conn.commit()
    cur.close()
    return render_template('analyze_face.html', feed=True, login=isLogin())

@app.route('/detect')
def detect():
    return render_template('analyze_face.html', feed=True, login=isLogin())

@app.route('/redetect/<int:id>')
def redetect(id):
    return render_template('analyze_face.html', feed=True, login=isLogin(), reana=True, mood_id=id)


@app.route("/login", methods=('GET', 'POST'))
def login():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        if not email:
            flash('Email is required!')
        elif not password:
            flash('Password is required!')
        else:
            cur = conn.cursor()
            cur.execute("select password, user_id, profile from users where email='%s'" % (email))
            res = cur.fetchall()
            conn.commit()
            cur.close()
            if len(res)>0 and bcrypt.verify(password, res[0][0]):
                session['user'] = res[0][1]
                session['profile'] = res[0][2]
                return redirect(url_for('home'))
            else:
                flash("Email or passowrd is wrong!")
    return render_template('login.html', login=True)


@app.route("/preference", methods=('GET', 'POST'))
def preference():

    if not session['user']:
        return redirect(url_for('login'))

    if request.method=="GET":
        cur = conn.cursor()
        cur.execute("select fun,sport,book,movie,songs from users where user_id=%s" % (session['user']))
        res = cur.fetchall()
        data = {"movie": res[0][2], "book": res[0][2],"songs": res[0][4],"sport": res[0][1],"fun": res[0][0] }
        return render_template('preference.html', data=data, login=isLogin())
    
    if request.method=="POST":
        pref = request.form.getlist('pref')
        if len(pref)<3:
             flash("Select at least 3")
        else:
            res = {"movie": False, "book": False,"songs": False,"sport": False,"fun": False }
            for i in pref:
                res[i] = True
            cur = conn.cursor()
            q = cur.mogrify("update users set movie=%s, songs=%s, book=%s, fun=%s, sport=%s where user_id=%s", (res["movie"],res["songs"],res["book"],res["fun"], res["sport"], session["user"]))
            cur.execute(q)
            conn.commit()
            cur.close()
            return redirect(url_for('genre_preference'))
        return render_template('preference.html', login=isLogin())

@app.route("/signup", methods=('GET', 'POST'))
def signup():
    if request.method=="POST":
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        date = request.form['date']
        file = request.files["file"]
        print(file.filename)
        if not email:
            flash('Email is required!')
        elif not password:
            flash('Password is required!')
        elif not name:
            flash('Name is required!')
        elif not date:
            flash('Birth Date is required!')
        elif not file:
            flash('Profile image is required!')
        else:
            hashed = bcrypt.hash(password)
            cur = conn.cursor()
            cur.execute("select * from users where email='%s'" % (email))
            res = cur.fetchall()
            if len(res)>0:
                flash('User Already Exist!')
            else:
                fname = str(uuid.uuid1()) + '.' + file.filename.split('.')[-1]
                print(fname)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                if validProfile(os.path.join(app.config['UPLOAD_FOLDER'], fname)):
                    date = date.split('-')
                    birth_date = psycopg2.Date(int(date[0]), int(date[1]), int(date[2]))
                    query = "insert into users (email, password, birth_date, name, profile) values ('%s','%s',%s,'%s','%s') returning user_id" % (email, hashed, birth_date, name, fname)
                    cur.execute(query)
                    user = cur.fetchall()
                    conn.commit()
                    cur.close() 
                    if user[0]:
                        session['user'] = res[0][1]
                        session['profile'] = fname
                        return redirect(url_for('preference'))
                    else:
                        flash('Something went wrong!')
                else:
                    flash('Image not accepted!')
    return render_template('signup.html', login=True)


@app.route("/logout")
def logout():
    session["user"] = None
    session["profile"] = None
    return render_template('home.html', login=True)

@app.route("/test")
def test():
    id =6
    face=[]
    valid=True
    mood="Happy"
    img="b3aa524a-e581-11ed-b802-38d57a841264.png"
    return render_template('analyze_face.html', face = face, mood=mood, img=img, valid=valid, login=isLogin(), reana=True, mood_id=id)


@app.route("/rating", methods=['POST'])
def rating():
    print("abc")
    if request.method=="POST":
        rate = request.form['rating']
        id = request.form['id']
        if rate:
            cur = conn.cursor()
            cur.execute("update mood set rating=%s where mood_id=%s" % (rate, id))
            conn.commit()
            cur.close()
            return redirect(url_for('history'))
        else:
            flash('Something went wrong!')
    return redirect(url_for('history'))


@app.route("/genres_preference", methods=('GET', 'POST'))
def genre_preference():

    if not session['user']:
        return redirect(url_for('login'))

    if request.method=="GET":
        gen = ["Drama", "Family", "Musical", "Fantasy", "Action", "Science Fiction", "Thriller", "Comedy", "Romance", "Horror", "Mystry","Adventure", "Sport", "History", "Travel"]
        cur = conn.cursor()
        cur.execute("select genre_pref from users where user_id=%s" % (session['user']))
        res = cur.fetchall()
        store = res[0][0].split(",")
        data = {}
        for i in gen:
            data[i] = i in store
        return render_template('genres.html', data=data, login=isLogin())
    
    if request.method=="POST":
        pref = request.form.getlist('pref')
        if len(pref)<7:
             flash("Select at least 7")
        else:
            res = ','.join(pref)
            cur = conn.cursor()
            q = cur.mogrify("update users set genre_pref=%s where user_id=%s", (res, session["user"]))
            cur.execute(q)
            conn.commit()
            cur.close()
            return redirect(url_for('home'))
        return render_template('genres.html', login=isLogin())

@app.route("/")
def home():
    return render_template('home.html', login=isLogin())





if __name__ =='__main__':  
    app.run(debug=True)