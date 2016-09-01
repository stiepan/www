var loggedin = false;

var show_loader = function () {
    var loader = $('<div></div>');
    loader.addClass('modal loader');
    $('body').append(loader);
};

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
    var err = $('.error').removeClass('fine');
    err.find('p').text(txt);
    err.show();
    setTimeout(function(){
        err.hide();
    }, 5000);
};

var fine =  function (txt) {
    var err = $('.error').addClass('fine');
    err.find('p').text(txt);
    err.show();
    setTimeout(function(){
        err.hide();
    }, 5000);
};

var confirm = function (txt, callback) {
    var confirm = $('.confirm');
    confirm.find('p').text(txt);
    confirm.find('.button_contr').off('click').on('click', function () {confirm.hide();});
    confirm.find('#confirm_ok').off('click').on('click', function () {
        callback();
        confirm.hide();
    });
    confirm.show();
};

var request = function (addr, type, params) {
    var type = typeof type === 'undefined'? 'GET' : type;
    var params = typeof params === 'undefined'? {} : params;
    params = JSON.stringify(params);
    return new Promise(function (resolve, reject) {
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
        if (res.candidates.length == 2) {
            drawMarkersMap(res.candidates[0].surname, res.candidates[1].surname);
        }
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
    if (cands.length == 2 && cands[0].results) {
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
            show_loader();
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
                var disabled = loggedin ? '' : 'disabled=""';
                show_loader();
                request('/municipality/' + param).then( function (res) {
                    if (res.status != 'OK') {
                        failwith(res.status);
                    }
                    else {
                        var munitr = $('<tr class="muni_details_row"></tr>');
                        var muni = $('<td colspan="8" class="muni_details"></td>');
                        var lastmod = 'nigdy';
                        $.each(res.attrs, function (k, v) {
                            var ddisplay = '';
                            var isin = ['last_modification', 'counter'].indexOf(k);
                            if (isin >= 0) {
                                ddisplay = 'style="display: none"';
                                if (isin == 0)
                                    lastmod = v.val;
                            }
                            muni.append('<div ' + ddisplay + ' class="det_item"><label for="muni___' + k + '">' + v.name + '</label>' +
                                '<input ' + disabled + ' type="text" name="muni___' + k + '" value="' + v.val + '"></div>')
                        });
                        if (loggedin) {
                            var contr = $('<div class="det_item contr"></div>')
                            contr.append('<a class="button_contr">Anuluj</a>').on('click', function () {
                                clicked.trigger('click');
                            });
                            contr.append($('<a class="button_contr" id="save_but">Zapisz</a>').on('click', function (e){
                                e.stopPropagation();
                                update_muni(param, lastmod);
                            }));
                            muni.append(contr);
                        }
                        clicked.addClass('clicked_row');
                        cont.animate({scrollTop: cont.scrollTop() - cont.offset().top + clicked.offset().top}, 500);
                        setTimeout(function () {
                            clicked.after(munitr.append(muni))
                        }, 500);
                    }
                    $('.loader').detach();
                });
            }
        }
        detail_prog = false;
    }
};

var loginForm = function () {
    loggedin = false;
    var form = $('<form></form>');
    var login = $('<input type="text" value="login" id="id_username" name="username">');
    var password = $('<input type="password" value="login" id="id_password" name="password">');
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
        show_loader();
        request('/login/', 'POST', {
            'username': $(this).find('[name=username]').val(),
            'password': $(this).find('[name=password]').val()
        }).then(function (res) {
            if (res.status == 'unrecognized') {
                failwith("Błędne dane logowania.");
            }
            else {
                var hi = $('<p>Witaj, '+res.username+'. </p>');
                var logout_but = $('<a id="logoutbut">Wyloguj się</a>').on('click', logout);
                $('.log section').empty().append(hi).append(logout_but);
                loggedin = true;
                fine("Zalogowano pomyślnie.");
            }
            $('.loader').detach();
        })
    });
    $('.log section').empty().append(form.append(login).append(password).append(submit));
};

var logout = function () {
    show_loader();
    request('/login/', 'POST', {'logout': true}).then(function (res) {
        if (res.status != 'loggedin') {
            loginForm();
            fine("Nastąpiło wylgowanie.");
        }
        else {
            failwith("Nieudane wylogowanie.")
        }
        $('.loader').detach()
    });
};

var update_muni = function (id, lastmod) {
    var date = new Date(lastmod);
    confirm("Czy na pewno chcesz zmodyfikować dane z " + date.toLocaleString("PL") + '?', function () {
        var els = $('.det_item input');
        var data = {};
        $.each(els, function (i, obj) {
            obj = $(obj);
            data[obj.prop('name').split('___')[1]] = obj.val();
        });
        data['id'] = id;
        show_loader();
        request('/municipality/', 'POST', data).then(function (res) {
            if (res.status != 'OK') {
                failwith(res.status);
                $('.loader').detach();
            }
            else {
                fine('Pomyślnie zapisano dane');
                $('.loader').detach();
            }
        });
    });
};

var update_content = function (){
    request('/results/').then(function (res) {
        localStorage.res = JSON.stringify(res);
        process_data(res);
        $('.loader').detach();
    }, function (err) {
        console.log(err);
    });
};

$(document).ready(function () {
    show_loader();
    if (localStorage.hasOwnProperty('res')) {
        process_data(JSON.parse(localStorage.res));
        $('.loader').detach();
    }
    update_content();
    $('.modal').on('click', function () {
        update_content();
        $('.modal, .modal_val').hide();
    });
    $(window).on('resize', function () {
        $('.modal_val .table_container').css('max-height', ($(window).height() - 70) + 'px');
    });
    request('/login/').then(function (res) {
        if (res.status != 'loggedin') {
            loginForm();
        }
        else {
            loggedin = true;
            var hi = $('<p>Wtiaj, '+res.username+'. </p>');
            var logout_but = $('<a id="logoutbut">Wyloguj się</a>').on('click', logout);
            $('.log section').empty().append(hi).append(logout_but);
        }
    }, function (err) {
        console.log(err);
    });
});