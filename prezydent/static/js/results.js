var cookie = function (name) {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
        var c = cookies[i].split('=');
        if (c[0] == name)
            return c[1];
    }
    return undefined;
};

var failwith =  function (txt) {
    var err = $('.error');
    err.find('p').text(txt);
    err.show();
    setTimeout(function(){
        err.hide();
    }, 5000);
};

var request = function (addr, type, params) {
    var type = typeof type === 'undefined'? 'GET' : type;
    var params = typeof params === 'undefined'? {} : params;
    params = JSON.stringify(params);
    var loader = $('<div></div>');
    loader.addClass('modal loader');
    return new Promise(function (resolve, reject) {
        if (!$('.modal.loader').length)
            $('body').append(loader);
        var req = new XMLHttpRequest();
        req.open(type, addr, true);
        if (type == 'POST') {
            req.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            req.setRequestHeader('X-CSRFToken', cookie('csrftoken'));
        }
        req.onload = function () {
            if (req.status == 200) {
                resolve(JSON.parse(req.response));
            }
            else {
                reject(Error(req.statusText));
            }
        };
        req.onerror = function () {
            reject(Error("Connection problem"));
        };
        req.send(params);
    });
};

var country_summary = function (res) {
    var summary = {'entitled': 0, 'valid_votes': 0, 'dwellers': 0, 'issued_cards': 0, 'votes': 0};
    $.each(res.quantile, function (i, obj) {
       $.each(summary, function (k) {
           summary[k] += obj.results[k];
       });
    });
    $.each(summary, function (k, v) {
        $('.'+k).text(v);
    });
    $('.density').text((summary['dwellers'] / 312685).toFixed(2));
    google.charts.setOnLoadCallback(function () {
        drawMarkersMap(res.candidates[0].surname, res.candidates[1].surname);
    });
};

var br = function (perc) {
    return '<div class="result_bar"><span class="difference" style="width: '+perc+'%"></span></div>'
};

var populate_table = function (type, obj, tableid, preserve) {
    var table = $('#'+tableid + ' tbody');
    if (typeof preserve === 'undefined')
        table.empty();
    $.each(obj, function (i, obj) {
        if (this.results.candidates.length) {
            var row = $('<tr></tr>').css('cursor', 'pointer');
            row.on('click', function () {
                detail(type, obj.id, this);
            });
            row.append($('<td></td>').text(i + 1).prop('id', type + '_' + this.id).addClass('voiv_code'));
            var res = this.results;
            $.each([this.name, res.valid_votes, res.candidates[0].votes, res.candidates[0].percentage,
                br(res.candidates[0].percentage), res.candidates[1].votes, res.candidates[1].percentage], function (j) {
                row.append($('<td></td>').html(this).addClass(type + '_col_' + (j + 1)));
            });
            table.append(row);
        }
    });
};

var aggregate = function () {
  var s = function (objs) {
      var res = 0;
      $.each(objs, function() {res += parseFloat($(this).text())});
      return res;
  };
  var a = function (objs) {
      var len = objs.length;
      return len ? (s(objs) / len).toFixed(2) : '-';
  };
  var b = function (objs) {
      var res = 0;
      var len = objs.length;
      $.each(objs, function() {
          res += 100*$(this).find('.difference').width()/$(this).width();
      });
      return len ? br(res / len) : '';
  };
  return {s: s, a: a, b: b};
};

var table_summary = function (tb_id, type, cols) {
    var tr = $('#' + tb_id +  ' tfoot tr').children();
    $.each(cols, function (i, spec) {
        if (spec != null) {
            $(tr[i]).html(spec($('.'+type+ '_col_' +i)));
        }
    });
};

var candidates = function (cands) {
    if (cands.length == 2) {
        $('.cand1').text(cands[0].surname.toUpperCase() + ' ' + cands[0].first_name);
        $('.cand2').text(cands[1].surname.toUpperCase() + ' ' + cands[1].first_name);
        $('.result_bar.first_cand .difference').css('width', cands[0].results.percentage + '%');
        $('.result_bar.second_cand .difference').css('width', cands[1].results.percentage + '%');
        $('.cand1_pr').text(cands[0].results.percentage + '%');
        $('.cand2_pr').text(cands[1].results.percentage + '%');
        $('.cand1_vt').text(cands[0].results.votes);
        $('.cand2_vt').text(cands[1].results.votes);
    }
};

var process_data = function (res) {
    candidates(res.candidates);
    populate_table('voiv', res.voivs, 'main_comparison');
    var a = aggregate();
    table_summary('main_comparison', 'voiv', [null, null, a.s, a.s, a.a, a.b, a.s, a.a]);
    country_summary(res);
    var $separator = $('#quantile_comparison .separate').detach();
    populate_table('type', res.types, 'quantile_comparison');
    $('#quantile_comparison').append($separator);
    populate_table('quant', res.quantile, 'quantile_comparison', true);
};

var detail_prog = false;

var detail = function(type, param, clicked) {
    if (!detail_prog) {
        detail_prog = true;
        if (type != 'muni') {
            request('/results/detailed/' + type + ',' + param).then(function (res) {
                if (res.status && res.status == "OK") {
                    populate_table('muni', res.muni, 'detailed');
                    $('.loader').detach();
                    $('.modal_val .table_container').css('max-height', ($(window).height() - 70) + 'px');
                    $('.modal_val thead td div').removeClass('clicked asc');
                    $('.modal_val thead td:first-child div').addClass('clicked');
                    $('.modal, .modal_val').show();
                }
                else {
                    console.log("Wystąpił błąd serwera w wyniku nieprawidłowego zapytania.");
                    console.log(res)
                }
            }, function (err) {
                console.log(err);
                $('.loader').detach();
            });
        }
        else {
            clicked = $(clicked);
            var cont = $('.table_container');
            var is_active = clicked.hasClass('clicked_row');
            $('.muni_details_row').remove();
            cont.find('.clicked_row').removeClass('clicked_row');
            if (!is_active) {
                clicked.addClass('clicked_row');
                var munitr = $('<tr class="muni_details_row"></tr>');
                var muni = $('<td colspan="8" class="muni_details"></td>');
                cont.animate({scrollTop: cont.scrollTop() - cont.offset().top + clicked.offset().top}, 500);
                setTimeout(function() {clicked.after(munitr.append(muni))}, 500);
            }
        }
        detail_prog = false;
    }
};

var loginForm = function () {
    var form = $('<form></form>');
    var login = $('<input type="text" value="login" name="username">');
    var password = $('<input type="password" value="login" name="password">');
    var submit = $('<input type="submit" value=">">');
    $.each([login, password], function(i, obj) {
        obj.on('focus', function () {
           if (this.value == 'login')
               this.value = '';
        });
        obj.on('blur', function () {
           if (this.value == '')
               this.value = 'login';
       });
    });
    form.on('submit', function(e) {
        e.preventDefault();
        request('/login/', 'POST', {
            'username': $(this).find('[name=username]').val(),
            'password': $(this).find('[name=password]').val()
        }).then(function (res) {
            if (res.status == 'unrecognized') {
                failwith("Błędne dane logowania.");
            }
            else {
                var hi = $('<p>Wtiaj, '+res.username+'. </p>');
                var logout_but = $('<a>Wyloguj się</a>').on('click', logout);
                $('.log section').empty().append(hi).append(logout_but);
            }
            $('.loader').detach();
        })
    });
    $('.log section').empty().append(form.append(login).append(password).append(submit));
};

var logout = function () {
    request('/login/', 'POST', {'logout': true}).then(function (res) {
        if (res.status != 'loggedin') {
            loginForm();
        }
        else {
            failwith("Nieudane wylogowanie.")
        }
        $('.loader').detach()
    });
};


$(document).ready(function () {
    request('/results/').then(function (res) {
        process_data(res);
    }, function (err) {
        console.log(err);
    });
    $('.modal').on('click', function () {
        $('.modal, .modal_val').hide();
    });
    request('/login/').then(function (res) {
        if (res.status != 'loggedin') {
            loginForm();
        }
        else {
            var hi = $('<p>Wtiaj, '+res.username+'. </p>');
            var logout_but = $('<a>Wyloguj się</a>').on('click', logout);
            $('.log section').empty().append(hi).append(logout_but);
        }
        $('.loader').detach();
    }, function (err) {
        $('.loader').detach();
        console.log(err);
    });
});