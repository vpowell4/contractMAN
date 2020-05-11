from flask import Flask, render_template,request
import json
import pyodbc 
from datetime import datetime 

app = Flask(__name__)

server = "RYANSPC\SQLEXPRESS"
database = "contractmanager"

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contracts")
def contracts():
    return render_template("contracts.html")

@app.route("/actors")
def actors():
    columns=["userid","role","organisation","workgroup","telephone","email","adminlevel",
                "active","createdt","updatedt"]
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};Server="+server+
                            ";Database="+database+
                            ";Trusted_Connection=yes;")
    cursor = cnxn.cursor()
    data=cursor.execute('SELECT * FROM Actors FOR JSON PATH').fetchone()
    cursor.commit()
    cursor.close()
    return render_template("actors.html",columns=columns,actordata="var actordata = "+data[0],
                            actorcolumns="columns:[{title:'Userid', field:'userid'}, \
                                {title:'Organisation', field:'organisation'}, \
                                {title:'Role', field:'role'}, \
                                {title:'Admin Level', field:'adminlevel'}, \
                                {title:'Active', field:'active',hozAlign:'center'}, \
                                {title:'Updated', field:'updatedt', sorter:'date', hozAlign:'center'}]")

@app.route('/actorupd', methods=['POST'])
def get_post_json():    
    data = request.get_json()
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};Server="+server+
                            ";Database="+database+
                            ";Trusted_Connection=yes;")
    cursor = cnxn.cursor()
    sql = "EXECUTE ACTORS_UPD @JSONINFO='"+json.dumps(data)+"'"
    print(sql)
    cursor.execute(sql)
    cursor.commit()
    cursor.close()
    return data

@app.route('/actordel', methods=['POST'])
def get_post_json():    
    data = request.get_json()
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};Server="+server+
                            ";Database="+database+
                            ";Trusted_Connection=yes;")
    cursor = cnxn.cursor()
    sql = ""
    print("Delete the record")
    #  cursor.execute(sql)
    cursor.commit()
    cursor.close()
    return data

if __name__ == "__main__":
    app.run(debug=False)