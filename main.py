from flask import Flask, render_template,request
import json
import pyodbc 
from datetime import datetime 

app = Flask(__name__)

current_userid = "vpowell4"
server = "RYANSPC\SQLEXPRESS"
database = "contractmanager"

def table_data(sql,type):
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};Server="+server+
                            ";Database="+database+";Trusted_Connection=yes;")
    cursor = cnxn.cursor() 
    if (type=="one") :
        data=cursor.execute(sql).fetchone()
    elif (type=="all") :
        data=cursor.execute(sql).fetchall()
    else :
        data=cursor.execute(sql)
    cursor.commit()
    cursor.close()
    return data

def table_meta(table,type):
    if (type=="columns") :
        cols=table_data("SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('dbo."+table+"')","all")
    columns=[]
    for row in cols:
        columns.append(row[0])
    return columns

@app.route("/")
def home():
    results=table_data("EXECUTE DASHBOARD_STATS","all")
    dialog=table_data("SELECT * FROM Dialog FOR JSON PATH","one")
    return render_template("home.html",contracts=results[1][3],attention=results[1][1], warning=results[1][2],
        issues=results[2][3],risks=results[3][3],changes=results[0][3],dialog=dialog)

@app.route("/404")
def page_not_found():
    return render_template("404.html")

@app.route("/config")
def config():
    return render_template("config.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contracts")
def contracts():
    action  = request.args.get('action', None)
    columns=table_meta(table="Contracts",type="columns")
    if (action==None):
        data=table_data("SELECT * FROM Contracts FOR JSON PATH","one")
    else :
        data=table_data("SELECT * FROM Contracts WHERE status='"+action+"' FOR JSON PATH","one")
    return render_template("contracts.html",columns=columns,data=data[0], id="contractid",userid=current_userid)

@app.route('/contract/upsert', methods=['POST'])
def contractupsert():
    data = request.get_json()
    result = table_data("EXECUTE CONTRACTS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    print(json.dumps(data))
    return data

@app.route('/contract/delete', methods=['POST'])
def contractdelete():    
    data = request.get_json()
    result = table_data("EXECUTE CONTRACTS_DELETE @CONTRACTID='"+data+"'","exe")
    return data

@app.route("/issues")
def issues():
    contracts=table_data("SELECT contractid, title FROM Contracts FOR JSON PATH","one")
    columns=table_meta(table="Issues",type="columns")
    data=table_data("SELECT * FROM Issues FOR JSON PATH","one")
    return render_template("issues.html",columns=columns,data=data[0],id="issueid",
            contracts=json.loads(contracts[0]),userid=current_userid)

@app.route("/issue/contractid/<cid>")
def issuesbyconttact(cid=id):
    data=table_data("SELECT * FROM Issues WHERE contractid='"+cid+"' FOR JSON PATH","one")
    if (data == None) :
        data=""
    else :
        data=data[0]
    columns=table_meta(table="Issues",type="columns")
    return render_template("issues.html",columns=columns,data=data,id="issueid",userid=current_userid)

@app.route('/issue/upsert', methods=['POST'])
def issueupsert():
    data = request.get_json()
    result = table_data("EXECUTE ISSUES_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/issue/delete', methods=['POST'])
def issuedelete():    
    data = request.get_json()
    result = table_data("EXECUTE ISSUES_DELETE @ISSUEID='"+data+"'","exe")
    return data

@app.route("/risks")
def contractrisks():
    contracts=table_data("SELECT contractid, title FROM Contracts FOR JSON PATH","one")
    columns=table_meta(table="Risks",type="columns")
    data=table_data("SELECT * FROM Risks FOR JSON PATH","one")
    return render_template("risks.html",columns=columns,data=data[0],id="riskid",
            contracts=json.loads(contracts[0]),userid=current_userid)

@app.route("/risk/contractid/<cid>")
def risksbyconttact(cid=id):
    data=table_data("SELECT * FROM Risks WHERE contractid='"+cid+"' FOR JSON PATH","one")
    if (data == None) :
        data=""
    else :
        data=data[0]
    columns=table_meta(table="Risks",type="columns")
    return render_template("Risks.html",columns=columns,data=data,id="riskid",
            userid=current_userid)

@app.route('/risk/upsert', methods=['POST'])
def riskupsert():
    data = request.get_json()
    result = table_data("EXECUTE RISKS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/risk/delete', methods=['POST'])
def riskdelete():    
    data = request.get_json()
    result = table_data("EXECUTE RISKS_DELETE @RISKID='"+data+"'","exe")
    return data

@app.route("/changes")
def contractchanges():
    contracts=table_data("SELECT contractid, title FROM Contracts FOR JSON PATH","one")
    columns=table_meta(table="Changes",type="columns")
    data=table_data("SELECT * FROM Changes FOR JSON PATH","one")
    if (data == None) :
        data=""
    else :
        data=data[0]
    return render_template("changes.html",columns=columns,data=data,id="changeid",
             contracts=json.loads(contracts[0]),userid=current_userid)    

@app.route("/change/contractid/<cid>")
def changesbyconttact(cid=id):
    data=table_data("SELECT * FROM Changes WHERE contractid='"+cid+"' FOR JSON PATH","one")
    if (data == None) :
        data=""
    else :
        data=data[0]
    columns=table_meta(table="Changes",type="columns")
    return render_template("Changes.html",columns=columns,data=data,id="changeid",userid=current_userid)

@app.route('/change/upsert', methods=['POST'])
def changeupsert():
    data = request.get_json()
    result = table_data("EXECUTE CHANGES_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/change/delete', methods=['POST'])
def changedelete():    
    data = request.get_json()
    result = table_data("EXECUTE CHANGES_DELETE @CHANGEID='"+data+"'","exe")
    return data

@app.route("/contract/contractid/<cid>")
def clause(cid=id):
    # Get the basic contract information
    contract=table_data("SELECT * FROM Contracts WHERE contractid='"+cid+"'FOR JSON PATH","one")
    # Get Contract Clauses for this contract
    data=table_data("SELECT * FROM Clauses WHERE contractid='"+cid+"' FOR JSON PATH","one")
    columns=table_meta(table="Clauses",type="columns")
    return render_template("contract.html",columns=columns,data=data[0],
                            contract=contract[0],
                            id="contractid",userid=current_userid)

@app.route("/suppliers")
def suppliers():
    columns=table_meta(table="Suppliers",type="columns")
    data=table_data("SELECT * FROM Suppliers FOR JSON PATH","one")
    return render_template("suppliers.html",columns=columns,data=data[0],id="email",userid=current_userid)

@app.route('/suppliers/upsert', methods=['POST'])
def supplierupsert():
    data = request.get_json()
    result = table_data("EXECUTE SUPPLIERS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/suppliers/delete', methods=['POST'])
def supplierdelete():    
    data = request.get_json()
    result = table_data("EXECUTE SUPPLIERS_DELETE @CHANGEID='"+data+"'","exe")
    return data

@app.route("/actors")
def actors():
    columns=table_meta(table="Actors",type="columns")
    data=table_data("SELECT * FROM Actors FOR JSON PATH","one")
    return render_template("actors.html",columns=columns,data=data[0],id="email",userid=current_userid)

@app.route('/actor/upsert', methods=['POST'])
def actorupsert():
    data = request.get_json()
    result = table_data("EXECUTE ACTORS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/actor/delete', methods=['POST'])
def actordelete():    
    data = request.get_json()
    result = table_data("EXECUTE ACTORS_DELETE @EMAIL='"+data+"'","exe")
    return data

if __name__ == "__main__":
    app.run(debug=False)