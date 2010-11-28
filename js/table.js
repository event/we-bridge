var player_positions = ["part", "right", "own", "left"];
var sides = ["N", "E", "S", "W"];
var suit_image_template = "<img src='images/{suit}.png' alt='{alt_suit}'/>";
var big_suit_image_template = "<img src='images/{suit}big.png' alt='{alt_suit}'/>";
var update_cnt = 1000;
var pass_dbl_rdbl = ["pass", "dbl", "rdbl"];

var lead_count;
var current_bidder;

var update_handlers = new Array();
update_handlers["move"] = process_lead;
update_handlers["bid"] = process_bid;
update_handlers["hand"] = process_hand;
update_handlers["start.bidding"] = kick_bidding;
update_handlers["start.play"] = kick_play;
update_handlers["end.play"] = end_play;

function on_body_load() {
    $("body").ajaxError(ajaxErrorHandler);
    $(document.documentElement).keypress(updator);
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
    handler = update_handlers[data.type];
    if (handler == undefined) {
	window.alert("action " + data.type + " is not yet supported!");
    } else {
	handler(data.value);
    }
}


function process_hand(v) {
    var player = v.player;
    var cards = v.cards;
    load_hand(player, cards);
}

function card_sort(c1, c2) {
    if (Math.floor(c1/13) + Math.floor(c2/13) == 1) {
	return c1 - c2;
    } else {
	return c2 - c1;
    }
}

function load_hand(player, cards) {
    var pos = $.inArray(player, player_positions);
    cards.sort(card_sort);
    var h = $("#" + player + "_hand");
    $.each(cards, 
	   function(idx, value) {
	       var s = document.createElement("span");
	       $(s).addClass("card card_" + player + " suit_" + Math.floor(value/13));
	       $(s).attr("id", "card_" + value)
	       var bg = "url(images/cards.png) " + (value * -71) +  "px 0";
	       $(s).css({"background": bg, "z-index": idx + 1, "left": idx * 6 + "%"});
	       h.append(s);
	   });
}

function process_bid(v) {
	var side = v.side;
	var bid = v.bid;
	var dbl_rdbl_allowed = v.dbl_mode;
	prohibit_bid("#bid_dbl.clickable");
	prohibit_bid("#bid_rdbl.clickable");
	if (dbl_rdbl_allowed == "dbl") {
	    allow_bid("#bid_dbl:not(.clickable)");
	} else if (dbl_rdbl_allowed == "rdbl") {
	    allow_bid("#bid_rdbl:not(.clickable)");
	}
	var bid_html;
	var idx = $.inArray(bid, pass_dbl_rdbl);
	if (idx == -1) {
	    var r = bid[0];
	    var s = bid[1];
	    if (s != 'Z') {
		var img = suit_image_template.replace("{suit}", s.toLowerCase()).replace("{alt_suit}", s);
		bid_html = r + img;
	    } else {
		bid_html = r + "NT";
	    }

	    disallow_lower_bids(parseInt(r), s);
	} else {
	    bid_html = bid;
	}
	$("#bidding_area tr:last td:eq(" + side + ")").html(bid_html);
	if (side == 3) {
	    $("#bidding_area").append("<tr class='bidding_row'><td></td><td></td><td></td><td></td></tr>")
	}
}

function prohibit_bid(bid_selector) {
    $(bid_selector).unbind("click").removeClass("clickable").addClass("prohibited_bid");
}

function allow_bid(bid_selector) {
    $(bid_selector).bind("click", do_bid).addClass("clickable").removeClass("prohibited_bid");
}

function disallow_lower_bids(r, s) {
    var bid_id = "bid_" + r + s;
    var allowed_bids = $(".clickable.bidbox_bid");
    var filtered = allowed_bids.filter(function(index){return this.id <= bid_id});
    filtered.unbind("click").removeClass("clickable").addClass("prohibited_bid");
}

function process_lead(v) {
    if (lead_count % 4 == 0) {
	for (var i = 0; i < 4; i += 1) {
	    $("#" + player_positions[i] + "_lead").html("&nbsp;");
   	}
    }

    var player = v.player;
    var card = v.card;
    var next = v.next;
    var allowed = v.allowed;
    if (allowed == null) {
	allowed = "any";
    }
    var card_div_id = "#card_" + card;
    var lead_div_id = "#" + player + "_lead";
    $(lead_div_id).append($(card_div_id).detach().removeClass("highlighted")
			  .css({"z-index": lead_count, "left": 0}));
    var np;
    if (next == null) {
	np = next_player(player);
    } else {
	var idx = $.inArray(next, player_positions);
	if (idx % 2 == 1) {
	    $("#their_tricks").text(trick_inc);
	} else {
	    $("#our_tricks").text(trick_inc);
	}
	np = next;
    }
    var np_class = ".card_" + np;
    $(".card").unbind("click").removeClass("clickable");
    if (allowed == 'any') {
	allow_cards(np_class, np);
    } else {
	var np_suit_class = np_class + ".suit_" + allowed;
	allow_cards(np_suit_class, np);
    }
    lead_count += 1;
}

function allow_cards(selector, player) {
    return $(selector).bind("click", player, highlight_for_lead)
	.bind("dblclick", player, do_lead).addClass("clickable");
}

function next_player(player) {
    var idx = $.inArray(player, player_positions);
    if (idx == 3) {
	return player_positions[0];
    } else {
	return player_positions[idx + 1];
    }
}

function do_lead(event) {
    var player = event.data;
    var splitted_id = event.target.id.split("_");
    var number = splitted_id[1];
    var url = "action.json?move/" + player + "/" + number;
    $.post(url);
}


function ajaxErrorHandler(event, xhr, opts, error) {
    // retry should be here for some requests
    window.alert("request failed");
}

function img_by_suit(suit) {
    var c = suit.charAt(0);
    return suit_image_template.replace("{suit}", c.toLowerCase()).replace("{alt_suit}", c.toUpperCase());
}

function kick_bidding(v) {
    $(".bidbox_bid,.bidbox_pass").bind("click", do_bid).addClass("clickable");
    prohibit_bid("#bid_dbl");
    prohibit_bid("#bid_rdbl");
    current_bidder = v.dealer;
    if (v.vuln & 1) {
	$(".vuln_NS").addClass("vulnerable");
    }

    if (v.vuln & 2) {
	$(".vuln_EW").addClass("vulnerable");
    }

    side = sides[v.dealer];
    $("#dealer_" + side).addClass("dealer");
	
}

function kick_play(v) {
    var contract = v.contract;
    var lead_maker = v.lead;
    var player = player_positions[lead_maker];
    lead_count = 0;
    $("#bidbox").css("display", "none").after($("#bidding_area").detach());
    $("#bidbox_cell").css("text-align", "center");

    $("#lead_area").removeClass("hidden");
    allow_cards(".card_" + player, player);
    var csuit = contract[1];
    var cntrct_html;
    if (csuit != "Z") {
	cntrct_html = contract[0] + 
	    big_suit_image_template.replace("{suit}", csuit.toLowerCase())
	    .replace("{alt_suit}", csuit.toUpperCase());;
    } else {
	cntrct_html = contract[0] + "NT";
    }
    $("#contract").html(cntrct_html + contract.substr(2, 2));
}

function highlight_for_lead(event) {
    var splitted_id = event.target.id.split("_");
    var number = splitted_id[1];
    allow_cards(".highlighted", event.data).removeClass("highlighted");
    $("#card_" + number).addClass("highlighted").bind("click", event.data, do_lead);    
}

function do_bid(event) {
    var splitted_id = event.currentTarget.id.split("_");
    var bid = splitted_id[1];
    
    var url = "action.json?bid/" + player_positions[current_bidder] + "/" + bid;
    current_bidder = (current_bidder + 1) % 4;
    $.post(url);
}

function trick_inc(i, s) {
    if (s.length == 0) {
	return 1;
    } else {
	return parseInt(s) + 1;
    }
}


function end_play(v) {
    $(".vuln_NS,.vuln_EW").removeClass("vulnerable");
    $("#dealer_N,#dealer_E,#dealer_S,#dealer_W").removeClass("dealer");
    $("#bidding_area").removeClass("hidden");
    $("#bidbox").css("display", "inline-block");
    $("#bidbox_cell").css("text-align", "right");
    $("#lead_area").addClass("hidden");
    $("#contract,.tricks").html("");
    $("#bidding_area tr:gt(1)").remove();
    $("#bidding_area tr:gt(0) td").text("");
    $(".bidbox_bid,.bidbox_pass,.bidbox_dbl,.bidbox_rdbl")
	.unbind("click").removeClass("prohibited_bid clickable");
    $(".lead").text("");
    $("#lead_area").before($("#bidding_area").detach());
    var contract = v.contract;
    var decl = v.declearer;
    var points = v.points;
    var tricks = v.tricks;
    var url = v.protocol_url;
    var sign = "";
    if (points > 0) {
	sign = "+";
    }
    var contract_html;
    var r = contract[0];
    var s = contract[1];
    if (s != 'Z') {
	var img = suit_image_template.replace("{suit}", s.toLowerCase()).replace("{alt_suit}", s);
	contract_html = r + img;
    } else {
	contract_html = r + "NT";
    }
    contract_html += contract.substr(2, 2);
    $("#popup_res").html("<a href='" + url + "' target='_blank'>" +  tricks 
			 + " tricks, " + sign + points + "</a>");
    $("#popup_contract").html(contract_html + " by " + decl);
    $(".popup").bPopup();
	
}