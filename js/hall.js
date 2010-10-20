var positions = ["N", "S", "E", "W"];
var empty_sit = "<a href=table.html?{id}>take a sit</a>";

function on_body_load() {
    $("body").ajaxError(ajaxErrorHandler);
    $(document.documentElement).keypress(updator)
}

function updator(event) {
    if (event.charCode == 32) {
	get_json();
    }
}

function get_json() {
    $.getJSON("update.json", function(data){$.each(data, process_update);});
}

function process_update(i, data) {
    if (data.type == "table.add"){
	$("#table_list").append("<tr class='table'><td class='player'></td><td class='player'></td>"
				+ "<td class='player'></td><td class='player'></td></tr>");
	$("#table_list tr:last td").each(function(i, e){
		$(e).append(empty_sit.replace("{id}", data.value + "/" + positions[i]))});
	$("#table_list tr:last").data("table_id", data.value);
    } else if (data.type == "table.remove") {
	$("#table_list tr:eq(" + (data.value + 1) + ")").remove();
    } else if (data.type == "player.sit") {
	var v = data.value;
	var table_num = v.table + 1;
	var name = v.name;
	var pos = v.position;
	$("#table_list tr:eq(" + table_num + ") td:eq(" + $.inArray(pos, positions) + ")").html(name);
    } else if (data.type == "player.leave") {
	var v = data.value;
	var table_num = v.table + 1;
	var pos = v.position;	
	var table_id = $("#table_list tr:eq(" + table_num + ")").data("table_id");
	$("#table_list tr:eq(" + table_num + ") td:eq(" + $.inArray(pos, positions) + ")")
	    .html(empty_sit.replace("{id}", table_id + "/" + pos));
    } else if (data.type == "text") {
	window.alert("text message is not supported yet!");
    }
}

function ajaxErrorHandler(event, xhr, opts, error) {
    // retry should be here for some requests
    window.alert("request failed");
}

