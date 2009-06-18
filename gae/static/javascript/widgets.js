// GLOBAL VARIABLES

var debug = false;

// GLOBAL FUNCTIONS

function pad(number, length) {
    var str = "" + number;
    while (str.length < length) {
        str = "0" + str;
    }
    return str;
};

// Templating

(function(){
    var cache = {};
    this.tmpl = function tmpl(str, data){
      var fn = !/\W/.test(str) ?
        cache[str] = cache[str] ||
          tmpl(document.getElementById(str).innerHTML) :
        new Function("obj",
          "var p=[],print=function(){p.push.apply(p,arguments);};" +
          "with(obj){p.push('" +
          str
            .replace(/[\r\t\n]/g, " ")
            .split("\[%").join("\t")
            .replace(/((^|%\])[^\t]*)'/g, "$1\r")
            .replace(/\t=(.*?)%\]/g, "',$1,'")
            .split("\t").join("');")
            .split("%\]").join("p.push('")
            .split("\r").join("\\'")
        + "');}return p.join('');");
      return data ? fn( data ) : fn;
    };
})(); 

// WIDGET: TEMPLATE PARAMETER

var wtp = {

    state: {
        row_count: 0,
    },

    init: function () {

        $("table#wtp").sortable();

        $("input.row_add").livequery("click", function () {
            wtp.addRow();
        });   

        $("input.row_copy").livequery("click", function () {
            wtp.copyRow($(this));
        });   

        $("input.wtp_validate").livequery("click", function () {
            wtp.saveJson($("textarea#id_parameters"));
        });   

        $("input.row_delete").livequery("click", function () {
            wtp.deleteRow($(this));
        });   

        $("select.step_type").livequery("change", function () {
            var src = $(this);
            var step_id = src.find("option:selected").attr("name");
            var html = "";
            for(i in step_types) {
                var step_type = step_types[i];
                html = html + "HELLO";
            }
            src.parent().find(".step_content").html(html);
        });   

    },

    loadJson: function(json) {

        console.log("Loading JSON");
        for(row_i in json) {
            var row = json[row_i];
            wtp.addRow();
            $("table#wtp tbody tr:last-child input.field_name").val(row.name);
            $("table#wtp tbody tr:last-child select.field_type").val(row.type);
            $("table#wtp tbody tr:last-child input.field_default").val(row.default);
        }

    },

    saveJson: function(el) {

        console.log("Saving JSON");
        var output = "";
        var row = $("table#wtp tbody tr");
        var row_count = wtp.state.row_count;
        console.log(row_count);
        var i = 1;
        output = "[";
        row.each(function () {
            var property = $(this); 
            output = output + '{';
            output = output + '"name": "'+property.find("input.field_name").val()+'",';
            output = output + '"type": "'+property.find("select.field_type :selected").val()+'",';
            output = output + '"default": "'+property.find("input.field_default").val()+'"';
            output = output + '}';
            if(i < row_count) { output = output + ","; }
            i++;
        });
        output = output + "]";
        $(el).val(output);

    },

    addRow: function() {

        console.log("Adding row");
        wtp.state.row_count++;
        $("table#wtp tbody").append(tmpl("tmpl_item_row", {}));

        wtp.renumber();

    },

    copyRow: function(src) {

        console.log("Copying row");
        wtp.state.row_count++;

        var cItem = src.parent();       
        cItem.after(cItem.clone());

        wtp.renumber();

    },

    deleteRow: function(src) {

        console.log("Deleting row");
        wtp.state.row_count--;
        
        var cRow = src.parent();
        cRow.remove();

        wtp.renumber();

    },

    renumber: function() {

        console.log("Renumbering");
        var i = 0;
        var row = $("table#wtp tbody tr");
        row.each(function () {
            i++;
        });
        wtp.state.row_count = i;

    }

}


