function start_updator(handler_array) {
    $.getJSON("channel.json", function(data){reg_channel(data, handler_array)});
}

function ping(){
    $.post("action.json?ping");
}

function onopen(){
    ping(); 
    window.setInterval(ping, 2 * 60 * 1000);
}

function reg_channel(chid, handlers) {
    var channel = new goog.appengine.Channel(chid);
    channel.open({"onmessage": function(data){process_update(data, handlers)}
	    , "onerror":  function(){start_updator(handlers);}
	    , "onopen": onopen, "onclose": function(){start_updator(handlers);}})
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
    if (handler != null) {
	handler(data.value);
    }
}
