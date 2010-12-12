function start_updator(handler_array) {
    init_channel(handler_array);
}

function init_channel(handlers) {
    $.getJSON("channel.json", function(data){reg_channel(data, handlers)});
}

function reg_channel(chid, handlers) {
    var channel = new goog.appengine.Channel(chid);
    channel.open({"onmessage": function(data){process_update(data, handlers)}, "onerror": process_error
		, "onopen": function(){}, "onclose": function(){}})
}

function process_error(e) {
    window.alert("Error: " + e.description);
}

function process_update(d, handlers) {
    var data = $.parseJSON(d.data);
    if (!$.isArray(data)) {
	data = [data];
    }
    $.each(data, function (){process_single_upd(this, handlers)});
}

function process_single_upd(data, handlers) {
    handler = handlers[data.type];
    if (handler == undefined) {
	window.alert("action " + data.type + " is not yet supported!");
    } else {
	handler(data.value);
    }
}
