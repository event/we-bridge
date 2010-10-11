

function on_body_load() {
    $("body").ajaxError(ajaxErrorHandler);
    $.getJSON("update.json", function(data){$.each(data, process_update)});
}


function process_update(i, data) {
    if (data.type == "lead"){
	window.alert("lead is not supported yet!");
    } else if (data.type == "bid") {
	window.alert("bid is not supported yet!");
    } else if (data.type == "text") {
	window.alert("text message is not supported yet!");
    } else if (data.type == "hand") {
	var v = data.value;
	var player = v.player;
	var suits = v.suits;
	$.each(suits, function(i, suit){load_suit(player, suit)})
    } else if (data.type == "claim") {
	window.alert("claim is not supported yet!");
    }
    // $.getJSON({"index.html#updates", function(data){$.each(data, process_update)}});
}

function load_suit(player, suit) {
    var s = suit.suit;
    var cards = suit.cards;
    var divid = "#" + player + "_" + s;
    $(divid).html(cards);
}


function ajaxErrorHandler(event, xhr, opts, error) {
    window.alert("request failed");
}