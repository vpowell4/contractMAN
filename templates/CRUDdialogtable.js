{% block CRUDdialogetable %}
var DialogData = $.ajax({
    type: "POST", dataType: "json", contentType: "application/json", async: false,
    url: "/getbasedata",
    data: JSON.stringify({module:'dialog',userid:userid,cid:cid,sid:sid,status:""}),
    success: function(results) {return results;},
    error: function(err) {console.log(err);}
    }).responseJSON;
if (DialogData==null) {
    DialogData=[]
    }
var DialogDataTable = new Tabulator("#DialogDataTable",{
    data:DialogData, addRowPos:"top",layout:"fitColumns",
    placeholder:"No dialogue data recorded",
    columns:[{title:"Type",field:"module",width:100, cellClick:function(e, cell){
                window.location.assign("/contractid?module="+cell.getRow().getData().module+
                    "&id="+cell.getRow().getData().contractid)}},
        {title:"Comments",field:"comments",width:600},
        {title:"upduserid",field:"upduserid",width:150},
        {title:"createdt",field:"createdt",width:150,formatter:"datetime",
                formatterParams:{outputFormat:"DD/MM/YY HH:MM",invalidPlaceholder:"(invalid date)"}},
        {title:"status",field:"status",
            width:100,formatter:function(cell, formatterParams){
            var value = cell.getValue();
            if(value == "Attention"){return "<span style='color:red;'>" + value + "</span>";}
            else if (value == "Warning"){return "<span style='color:orange;'>" + value + "</span>";}
            else {return "<span style='color:green;'>" + value + "</span>";}}}
        ],
        rowDblClick:function(e, row){
            var selectedData = table.getSelectedData()[0];
            dialogmodal.style.display = "block";
            }
        });
{% endblock %}