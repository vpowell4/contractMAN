from flask import Flask, render_template,request
import json
import pyodbc 
from datetime import datetime 

app = Flask(__name__)

current_userid = "vpowell"
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
    return render_template("home.html")

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
    columns=table_meta(table="Contracts",type="columns")
    data=table_data("SELECT * FROM Contracts FOR JSON PATH","one")
    return render_template("contracts.html",columns=columns,data=data[0], id="contractid",userid=current_userid)

@app.route('/contract/upsert', methods=['POST'])
def contractupsert():
    data = request.get_json()
    result = table_data("EXECUTE CONTRACTS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return data

@app.route('/contract/delete', methods=['POST'])
def contractdelete():    
    data = request.get_json()
    result = table_data("EXECUTE CONTRACTS_DELETE @CONTRACTID='"+data+"'","exe")
    return data

@app.route("/contract/contractid/<cid>")
def contract(cid=id):
    # Get the basic contract information
    contract=table_data("SELECT * FROM Contracts WHERE contractid='"+cid+"'FOR JSON PATH","one")
    # Get Contract Clauses for this contract
    data=table_data("SELECT * FROM ContractItems WHERE contractid='"+cid+"' FOR JSON PATH","one")
    columns=table_meta(table="ContractItems",type="columns")
    return render_template("contract.html",columns=columns,data=data[0],
                            contract=contract[0],id="contractid",userid=current_userid)

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