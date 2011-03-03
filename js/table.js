var sides = ["N", "E", "S", "W"];
var suit_image_template = "<img src='images/{suit}.png' alt='{alt_suit}'/>";
var big_suit_image_template = "<img src='images/{suit}big.png' alt='{alt_suit}'/>";
var pass_dbl_rdbl = ["pass", "dbl", "rdbl"];

var lead_count;
var my_side;
var tid;
var ind_int = window.setInterval(function(){}, 9999);
var first_deal = true;

var update_handlers = new Array();
update_handlers["move"] = process_move;
update_handlers["bid"] = process_bid;
update_handlers["hand"] = process_hand;
update_handlers["player.sit"] = user_sit;
update_handlers["player.leave"] = user_leave;
update_handlers["tricks"] = show_tricks;
update_handlers["start.bidding"] = kick_bidding;
update_handlers["start.play"] = kick_play;
update_handlers["end.play"] = end_play;
update_handlers["chat.add"] = handle_chat_add;
update_handlers["chat.message"] = handle_table_chat_message;

function on_body_load() {
    $("body").ajaxError(ajaxErrorHandler);
    parse_params();
    start_updator(update_handlers);
    $("#table").data("wid", "table_" + tid);
    init_chat();
    $("#alert_text").width($("#bidbox").width());
    $("#popup_res").text("Waiting for partners");
    $(".popup").bPopup();
}

function parse_params() {
    params = location.search.split("/");
    tid = params[0].substr(1);
    if (params.length > 1) {
	my_side = $.inArray(params[1], sides);
    }
}

function ajaxErrorHandler(event, xhr, opts, error) {
    // retry should be here for some requests
    window.alert("operation failed");
}

function process_hand(v) {
    var side = v.side;
    var cards = v.cards;
    cards.sort(card_sort);
    var h = $("#" + side + "_hand");
    h.children().remove();
    $.each(cards, 
	   function(idx, value) {
	       h.append(create_card(side, value).css({"z-index": idx + 1, "left": idx * 9 + "%"}));
	   });
}

function card_sort(c1, c2) {
    if (Math.floor(c1/13) + Math.floor(c2/13) == 1) { /* show clubs before diamonds */
	return c1 - c2;
    } else {
	return c2 - c1;
    }
}

function create_card(side, card) {
    var s = document.createElement("span");
    $(s).addClass("card card_" + side + " suit_" + Math.floor(card/13));
    $(s).attr("id", "card_" + card);
    var bg = "url(images/cards.png) " + (card * -71) +  "px 0";
    return $(s).css("background", bg);
}

function indicator(selector, interval) {
    $(selector).toggleClass("indicator");
    window.setTimeout(function(){$(selector).toggleClass("indicator");}, interval);
}

function indicate_turn(side, my_turn) {
    window.clearInterval(ind_int)
    if (my_turn) {
	window.focus();
    }
    ind_int = window.setInterval(function(){indicator("." + side + "_user", 500)}, 1000);
}

function process_bid(v) {
    var side = v.side;
    var bid = v.bid;
    var alert = v.alert;
    var dbl_rdbl_allowed = v.dbl_mode;
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
    var bid_cell = $("#bidding_area tr:last td:eq(" + side + ")");
    bid_cell.html(bid_html);
    if (alert != null) {
	bid_cell.CreateBubblePopup({innerHtml: decodeURIComponent(alert), themePath: "images/popup-themes"})
	    .addClass("alert_bid");
    }
    if (side == 3) {
	$("#bidding_area").append("<tr class='bidding_row'><td></td><td></td><td></td><td></td></tr>");
    }
    ns = (side + 1) % 4;
    var my_turn = ns == my_side;
    indicate_turn(sides[ns], my_turn);
    if (my_turn) {
	if (dbl_rdbl_allowed == "dbl") {
	    allow_bid("#bid_dbl");
	} else if (dbl_rdbl_allowed == "rdbl") {
	    allow_bid("#bid_rdbl");
	}
	allow_bid(".bidbox_pass");
	$(".bidbox_bid:not(.prohibited_bid)").bind("click", do_bid).addClass("clickable");
    } else if (side == my_side) {
	$("#alert_text").val("Alert");
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
    var allowed_bids = $(".bidbox_bid:not(.prohibited_bid)");
    var filtered = allowed_bids.filter(function(index){return this.id <= bid_id});
    filtered.addClass("prohibited_bid");
}

function process_move(v) {
    if (lead_count % 4 == 0) {
	for (var i = 0; i < 4; i += 1) {
	    $("#" + sides[i] + "_last span").remove();
	    $("#" + sides[i] + "_last")
		.append($("#" + sides[i] + "_lead span").detach());
   	}
	lead_count = 0;
    }

    var side = v.side;
    var card = v.card;
    var allowed = v.allowed;
    var trick = v.trick;
    var card_div_id = "#card_" + card;
    var lead_div_id = "#" + side + "_lead";
    if (trick != null) {
	$("#" + trick + "_tricks").text(trick_inc);
    }

    $(card_div_id).remove();
    var topv = 0;
    var sidedif = Math.abs(my_side - $.inArray(side, sides));
    if (sidedif == 3) {
	sidedif = 1;
    }
    topv += sidedif * 5;
    $(lead_div_id).append(create_card(side, card).css({"z-index": lead_count, "left": 0, "top": topv+"px"}));
    lead_count += 1;
    var np;
    if (v.next != null) {
	ns = v.next;
    } else {
	ns = next_side(side);
    }
    var my_turn = allowed != null;
    indicate_turn(ns, my_turn);
    if (!my_turn) {
	prohibit_cards(".card");
	return;
    }
    prohibit_cards(".card");
    if (allowed == "any") {
	allow_cards(".card_" + ns, ns);
    } else {
	var np_suit_class = ".card_" + ns + ".suit_" + allowed;
	allow_cards(np_suit_class, ns);
    }
}

function prohibit_cards(selector) {
    return $(selector).unbind("click dblclick").removeClass("clickable");
}

function allow_cards(selector, side) {
    return $(selector).bind("click", side, highlight_for_move)
	.bind("dblclick", side, do_move).addClass("clickable");
}

function next_side(side) {
    var idx = $.inArray(side, sides);
    return sides[(idx + 1) % 4]
}

function do_move(event) {
    var side = event.data;
    var splitted_id = event.target.id.split("_");
    var number = splitted_id[1];
    var url = "action.json?move/" + tid + "/" + side + "/" + number;
    $.post(url);
    prohibit_cards(".card");
    $(event.target).remove();
}


function img_by_suit(suit) {
    var c = suit.charAt(0);
    return suit_image_template.replace("{suit}", c.toLowerCase()).replace("{alt_suit}", c.toUpperCase());
}

function kick_bidding(v) {
    if (first_deal) {
	$(".popup").bPopup().close();
	first_deal = false;
    }
    prohibit_bid(".bidbox_pass,.bidbox_dbl,.bidbox_rdbl");
    if (v.vuln & 1) {
	$(".vuln_NS").addClass("vulnerable");
    }

    if (v.vuln & 2) {
	$(".vuln_EW").addClass("vulnerable");
    }

    side = sides[v.dealer];
    indicate_turn(side);
    $("#dealer_" + side).addClass("dealer");
    if (my_side == v.dealer) {
    	$(".bidbox_bid").bind("click", do_bid).addClass("clickable");
	allow_bid(".bidbox_pass");
    }
}

function kick_play(v) {
    var contract = v.contract;
    var lead_maker = v.lead;
    lead_count = 0;
    $("#bidbox").css("display", "none").after($("#bidding_area").detach());
    $("#alert_text").addClass("hidden");
    $("#bidbox_cell").css("text-align", "center");
    $("#lead_area").removeClass("hidden");
    indicate_turn(sides[lead_maker]);
    if (lead_maker == my_side) {
	s = sides[my_side];
	allow_cards(".card_" + s, s);
    }
    var csuit = contract[1];
    var cntrct_html;
    if (csuit != "Z") {
	cntrct_html = contract[0] + 
	    big_suit_image_template.replace("{suit}", csuit.toLowerCase())
	    .replace("{alt_suit}", csuit.toUpperCase());
    } else {
	cntrct_html = contract[0] + "NT";
    }
    $("#contract").html(cntrct_html);
    $("#contract_by").text(" by " + contract.substr(contract.length - 1))
}

function highlight_for_move(event) {
    var splitted_id = event.target.id.split("_");
    var number = splitted_id[1];
    allow_cards(".highlighted", event.data).removeClass("highlighted");
    $("#card_" + number).addClass("highlighted").bind("click", event.data, do_move);    
}

function do_bid(event) {
    var splitted_id = event.currentTarget.id.split("_");
    var bid = splitted_id[1];
    $(".bidbox_bid:not(.prohibited_bid)").unbind("click").removeClass("clickable");
    prohibit_bid(".bidbox_pass,.bidbox_dbl,.bidbox_rdbl");
    var url = "action.json?bid/" + tid + "/" + my_side + "/" + bid;
    var alert = $("#alert_text").val();
    if (alert != "" && alert != "Alert") {
	url += "/" + alert;
    }
    $.post(url);
}

function trick_inc(i, s) {
    if (s.length == 0) {
	return 1;
    } else {
	return parseInt(s) + 1;
    }
}

function show_tricks(v) {
    if (v.NS > 0) {
	$("#NS_tricks").text(v.NS);
    }
    if (v.EW > 0) {
	$("#EW_tricks").text(v.EW);
    }
}

function end_play(v) {
    $(".vuln_NS,.vuln_EW").removeClass("vulnerable");
    $("#dealer_N,#dealer_E,#dealer_S,#dealer_W").removeClass("dealer");
    $("#bidding_area").removeClass("hidden");
    $("#bidbox").css("display", "inline-block");
    $("#bidbox_cell").css("text-align", "right");
    $("#lead_area").addClass("hidden");
    $("#contract,#contract_by,.tricks").html("");
    $("#bidding_area tr:gt(1)").remove();
    $("#bidding_area tr td").text("").RemoveBubblePopup().removeClass("alertBid");
    $("#alert_text").removeClass("hidden");
    $(".hand_container").children().remove();
    $(".hand_container").append($("<img src='images/back.png' class='hand_mock'></img>"));
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
    if (contract == "pass"){
	contract_html = "pass";
    } else {
	var r = contract[0];
	var s = contract[1];
	if (s != "Z") {
	    var img = suit_image_template.replace("{suit}", s.toLowerCase()).replace("{alt_suit}", s);
	    contract_html = r + img;
	} else {
	    contract_html = r + "NT";
	}
    }
    contract_html += contract.substr(2, 2);
    $("#popup_res").html("<a href='" + url + "' target='_blank'>" +  tricks 
			 + " tricks, " + sign + points + "</a>");
    $("#popup_contract").html(contract_html + " by " + decl);
    $(".popup").bPopup();
}

function user_sit(v) {
    if (v.tid == tid) {
	var pos = v.position;
	var name = v.name;
	$("." + pos + "_user").text(name);
    }
}

function user_leave(v) {
    if (v.tid == tid) {
	var pos = v.position;
	$("." + pos + "_user").text("");
    }
}

function handle_table_chat_message(v) {
    var wid = v.wid;
    var idx = wid.indexOf("@");
    if (idx >= 0) {
	wid = wid.substr(0, idx);
    }
    if (wid != $("." + sides[(my_side + 2) % 4] + "_user").text()) {
	handle_chat_message(v);
    }
}
