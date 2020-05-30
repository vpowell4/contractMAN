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
# Which contracts is this person allowed to see ?
        if (content['module']=="actor") :
            execstring="SELECT * FROM "+content["module"].title()+"s"
        elif (content['module']=="supplier") :
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
        if (data==None):
            data[0]=""
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
        i.append(row[0]);
        r.append(row[1]);
        c.append(row[2]);
        s.append(row[3]);
        t.append(row[4]);
    results=table_data("EXECUTE DASHBOARD_STATS  @CURRENT_USER='"+session['current_user']+"'","all")
    return render_template("home.html",contracts=results[1][3],attention=results[1][1], warning=results[1][2],
        issues=results[2][3],risks=results[3][3],changes=results[0][3],userid=session['current_user'],
        stats={'issues':i,'risks':r,'changes':c,'suppliers':s,'contracts':t})

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/assessments")
@login_required
def assessments():
    return render_template("assessments.html")


@app.route("/contracts")
@login_required
def contracts():
    status=request.args.get('action', '')
    columns=table_meta(table="Contracts",type="columns")
    return render_template("contracts.html",columns=columns,status=status,
                sid="",cid="", id="contractid",userid=session['current_user'])

@app.route('/contract/upsert', methods=['POST'])
@login_required
def contractupsert():
    data = request.get_json()
    result = table_data("EXECUTE CONTRACTS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/contract/delete', methods=['POST'])
@login_required
def contractdelete():    
    data = request.get_json()
    result = table_data("EXECUTE CONTRACTS_DELETE @CONTRACTID='"+data+"'","exe")
    return data

@app.route("/contract/contractid/<cid>")
@login_required
def clause(cid=id):
    # Get the basic contract information
    contract=table_data("SELECT * FROM Contracts WHERE contractid='"+cid+"'FOR JSON PATH","one")
    columns=table_meta(table="Clauses",type="columns")
    return render_template("contract.html",columns=columns,status="",cid=cid,sid="",
                            contract=contract[0],id="contractid",userid=session['current_user'])


@app.route("/issues")
@login_required
def issues():
    contracts=table_data("SELECT contractid, title FROM Contracts FOR JSON PATH","one")
    columns=table_meta(table="Issues",type="columns")
    return render_template("issues.html",columns=columns,id="issueid",cid="",
            contracts=json.loads(contracts[0]),userid=session['current_user'])

@app.route("/issue/contractid/<cid>")
@login_required
def issuesbyconttact(cid=id):
    columns=table_meta(table="Issues",type="columns")
    return render_template("issues.html",columns=columns,
            status="",cid=cid,sid="",id="issueid",userid=session['current_user'])

@app.route('/issue/upsert', methods=['POST'])
@login_required
def issueupsert():
    data = request.get_json()
    result = table_data("EXECUTE ISSUES_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/issue/delete', methods=['POST'])
@login_required
def issuedelete():    
    data = request.get_json()
    result = table_data("EXECUTE ISSUES_DELETE @ISSUEID='"+data+"'","exe")
    return data

@app.route("/risks")
@login_required
def contractrisks():
    contracts=table_data("SELECT contractid, title FROM Contracts FOR JSON PATH","one")
    columns=table_meta(table="Risks",type="columns")
    return render_template("risks.html",columns=columns,id="riskid",
            contracts=json.loads(contracts[0]),userid=session['current_user'])

@app.route("/risk/contractid/<cid>")
@login_required
def risksbyconttact(cid=id):
    columns=table_meta(table="Risks",type="columns")
    return render_template("Risks.html",columns=columns,status="",cid=cid,sid="",id="riskid",userid=session['current_user'])

@app.route('/risk/upsert', methods=['POST'])
@login_required
def riskupsert():
    data = request.get_json()
    result = table_data("EXECUTE RISKS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/risk/delete', methods=['POST'])
@login_required
def riskdelete():    
    data = request.get_json()
    result = table_data("EXECUTE RISKS_DELETE @RISKID='"+data+"'","exe")
    return data

@app.route("/changes")
@login_required
def contractchanges():
    contracts=table_data("SELECT contractid, title FROM Contracts FOR JSON PATH","one")
    columns=table_meta(table="Changes",type="columns")
    return render_template("changes.html",columns=columns,id="changeid",cid="",
             contracts=json.loads(contracts[0]),userid=session['current_user'])    

@app.route("/change/contractid/<cid>")
@login_required
def changesbyconttact(cid=id):
    columns=table_meta(table="Changes",type="columns")
    return render_template("Changes.html",columns=columns,status="",
            cid=cid,sid="",id="changeid",userid=session['current_user'])

@app.route('/change/upsert', methods=['POST'])
@login_required
def changeupsert():
    data = request.get_json()
    result = table_data("EXECUTE CHANGES_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/change/delete', methods=['POST'])
@login_required
def changedelete():    
    data = request.get_json()
    result = table_data("EXECUTE CHANGES_DELETE @CHANGEID='"+data+"'","exe")
    return data


@app.route("/suppliers")
@login_required
def suppliers():
    columns=table_meta(table="Suppliers",type="columns")
    return render_template("suppliers.html",columns=columns,id="supplierid",userid=session['current_user'])

@app.route('/supplier/upsert', methods=['POST'])
@login_required
def supplierupsert():
    data = request.get_json()
    result = table_data("EXECUTE SUPPLIERS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/supplier/delete', methods=['POST'])
@login_required
def supplierdelete():
    data = request.get_json()
    result = table_data("EXECUTE SUPPLIERS_DELETE @SUPPLIERID='"+data+"'","exe")
    return data

@app.route("/actors")
@login_required
def actors():
    columns=table_meta(table="Actors",type="columns")
    return render_template("actors.html",columns=columns,id="email",userid=session['current_user'])

@app.route('/actor/upsert', methods=['POST'])
@login_required
def actorupsert():
    data = request.get_json()
    result = table_data("EXECUTE ACTORS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/actor/delete', methods=['POST'])
@login_required
def actordelete():    
    data = request.get_json()
    result = table_data("EXECUTE ACTORS_DELETE @EMAIL='"+data+"'","exe")
    return data

@app.route("/access/contractid/<cid>")
@login_required
def accessbycontract(cid=id):
    columns=table_meta(table="Accesss",type="columns")
    actors=table_data("SELECT actorid, email FROM Actors FOR JSON PATH","one")
    return render_template("accesss.html",columns=columns,actors=json.loads(actors[0]),
                cid=cid,userid=session['current_user'])

@app.route('/access/upsert', methods=['POST'])
@login_required
def accessupsert():
    data = request.get_json()
    result = table_data("EXECUTE ACCESSS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/dialog/insert', methods=['POST'])
@login_required
def dialoginsert():
    data = request.get_json()
    result = table_data("EXECUTE DIALOGS_INSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

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

if __name__ == "__main__":
    app.run(debug=False)