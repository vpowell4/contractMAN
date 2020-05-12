from flask import Flask, render_template,request
import json
import pyodbc 
from datetime import datetime 

app = Flask(__name__)

server = "RYANSPC\SQLEXPRESS"
database = "contractmanager"

def table_data(table,sql,type):
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

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/config")
def config():
    return render_template("config.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contracts")
def contracts(table="Contracts"):
    cols=table_data(table,"SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('dbo."+table+"')","all")
    columns=[]
    for row in cols:
        columns.append(row[0])
    print(columns)
    data=table_data(table,"SELECT * FROM Contracts FOR JSON PATH","one")
    return render_template("contracts.html",columns=columns,data=data[0])

@app.route('/contract/upsert', methods=['POST'])
def contractupsert(table="Contracts"):
    data = request.get_json()
    result = table_data(table,"EXECUTE CONTRACTS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return result

@app.route('/contract/delete', methods=['POST'])
def contractdelete(table="Contracts"):    
    data = request.get_json()
    result = table_data(table,"EXECUTE CONTRACTS_DELETE @EMAIL='"+data+"'","exe")
    return result

@app.route("/actors")
def actors(table="Actors"):
    cols=table_data(table,"SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('dbo."+table+"')","all")
    columns=[]
    for row in cols:
        columns.append(row[0]) 
    data=table_data(table,"SELECT * FROM Actors FOR JSON PATH","one")
    return render_template("actors.html",columns=columns,data=data[0])

@app.route('/actor/upsert', methods=['POST'])
def actorupsert(table="Actors"):
    data = request.get_json()
    result = table_data(table,"EXECUTE ACTORS_UPSERT @JSONINFO='"+json.dumps(data)+"'","exe")
    return result

@app.route('/actor/delete', methods=['POST'])
def actordelete(table="Actors"):    
    data = request.get_json()
    result = table_data(table,"EXECUTE ACTORS_DELETE @EMAIL='"+data+"'","exe")
    return result

if __name__ == "__main__":
    app.run(debug=False)