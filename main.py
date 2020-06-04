from flask import Flask, g, render_template,request,jsonify,flash,redirect,url_for,session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import pyodbc 
from datetime import datetime 

app = Flask(__name__)
app.secret_key = 'super really string'  # Change this!

def table_data(sql,type):
    server = "RYANSPC\SQLEXPRESS"
    database = "contractmanager"
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};Server="+server+
                            ";Database="+database+";Trusted_Connection=yes;")
    cnxn.timeout = 60  
    cursor = cnxn.cursor() 
    if (type=="one") :
        try:
            data=cursor.execute(sql).fetchone()
        except Exception as e:
            print("==>",e)
    elif (type=="all") : 
        try:
            data=cursor.execute(sql).fetchall()
        except Exception as e:
            print("==>",e)
    else : 
        try:
            data=cursor.execute(sql)
        except Exception as e:
            print("==>",e)
    cursor.commit()
    cursor.close()
    return data

@app.route("/getbasedata", methods=['POST'])
def getbasedata():
    if request.method == 'POST':
        content = request.get_json()
#        print(json.dumps(content))
# Which contracts is this person allowed to see ?
        if (content['module'] in ["actor","supplier"]) :
            execstring="SELECT * FROM "+content["module"].title()+"s"
        else :
            contracts="(SELECT contractid FROM accesss where actorid = (SELECT actorid FROM Actors WHERE email='"+session['current_user']+"'))"
            execstring="SELECT * FROM "+content["module"].title()+"s WHERE contractid in "+contracts
            if (content["status"]!=""):
                execstring=execstring+" AND status='"+content["status"]+"'"
            elif (content["cid"]!=""):
                execstring=execstring+" AND contractid='"+str(content["cid"])+"'"
            elif (content["sid"]!="" ):
                execstring=execstring+" AND supplierid='"+str(content["sid"])+"'"
        data=table_data("SELECT CAST(("+execstring+" FOR JSON PATH) AS VARCHAR(MAX))","one")
        for row in data :
            if (row==None) : data[0]="ERROR"
        return data[0]

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def usersload():
    data=table_data("SELECT CAST((SELECT email,actorid,password FROM Actors WHERE active='yes' FOR JSON PATH) AS VARCHAR(MAX))","one")
    user={}
    for row in json.loads(data[0]) :
        user[row['email']]={'password':row['password']}
    return user

users=usersload()

class User(UserMixin):
    pass
@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return 'no user'
    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return 'no user'
    user = User()
    user.id = email
    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    #user.is_authenticated = request.form['password'] == users[email]['password']
    return user

@app.route('/login',methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    email = request.form['email']
    if (email in list(users.keys())) :
        if request.form['password'] == users[email]['password']:
            user = User()
            user.id = email
            login_user(user)
            session['logged_in'] = True
            session['current_user'] = email
            return redirect(url_for('home'))
        else : 
            print("NO SUCH USER")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    user = current_user
    user.authenticated = False
    logout_user()
    session['logged_in'] = False
    return redirect(url_for('login'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("login.html")

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
            return render_template("register.html")
    email = request.form['email']
    userid = request.form['userid']
    password = request.form['password']
    data={'userid':userid,'password':password,'email':email}
    result = table_data("EXECUTE REGISTER_INSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return render_template("register.html")

def table_meta(table,type):
    if (type=="columns") :
        cols=table_data("SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('dbo."+table+"')","all")
    columns=[]
    for row in cols:
        columns.append(row[0])
    return columns

@app.route("/")
@app.route("/home")
@login_required
def home():
    stats = table_data("EXECUTE DASHBOARD_STATS02 @CURRENT_USER='"+session['current_user']+"'","all")
    i=[]; r=[]; c=[]; s=[];  t=[]
    for row in stats:
        i.append(row[0]); r.append(row[1]); c.append(row[2]); s.append(row[3]); t.append(row[4]);
    results=table_data("EXECUTE DASHBOARD_STATS  @CURRENT_USER='"+session['current_user']+"'","all")
    return render_template("home.html",contracts=results[1][3],attention=results[1][1], warning=results[1][2],
        issues=results[2][3],risks=results[3][3],changes=results[0][3],userid=session['current_user'],
        stats={'issues':i,'risks':r,'changes':c,'suppliers':s,'contracts':t})

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/views")
@login_required
def views():
    contracts=table_data("SELECT contractid, title FROM Contracts FOR JSON PATH","one")
    actors=table_data("SELECT actorid, email FROM Actors FOR JSON PATH","one")
    status=request.args.get('status', '')
    module=request.args.get('action', '')
    cid=request.args.get('cid', '')
    columns=table_meta(table=module+"s",type="columns")
    if (module=="actor") : mid="email"
    else : mid=module+"id"
    return render_template("views.html",columns=columns,id=mid,cid=cid,status=status,module=module,
        actors=json.loads(actors[0]),contracts=json.loads(contracts[0]),userid=session['current_user'])

@app.route('/deletedata', methods=['POST'])
@login_required
def deletedata():    
    data = request.get_json()
    contractid=""
    if (data['module'] in ['issue','change','risk','access','contract']) :
        contractid=str(data['contractid'])        
    result = table_data("EXECUTE "+data['module']+"S_DELETE @ID='"+data['id']+
                        "',@USERID='"+data['userid']+
                            "',@CONTRACTID='"+contractid+"'","exe")
    return data

@app.route('/upsertdata', methods=['POST'])
@login_required
def upsertdata():
    data = request.get_json()
    cmodule=data['module']
    if (request.args.get('action', '')=="dialog") :
        cmodule="dialog"
    result = table_data("EXECUTE "+cmodule+"S_UPSERT @JSONINFO='"+json.dumps(data)+
                            "',@USERID='"+data['upduserid']+
                            "',@CONTRACTID='"+str(data['contractid'])+"'","exe")
    return data

if __name__ == "__main__":
    app.run(debug=False)    