/**
 * Created by kamil on 22.08.16.
 */

var sort = function(tdid, col_nmb, asc) {
    var getText = function (el) {
        return el.contents().filter(function () {
            return this.nodeType == 3;
        })[0].nodeValue
    };
    var neg = (asc)? function(x){return x * (-1)} : function (x) {return x};
    var parent = $('#'+ tdid +' tbody');
    var rows = parent.find('tr');
    var upd = rows.sort(function(a, b) {
        var atds = $('td', a);
        var btds = $('td', b);
        if($(atds[col_nmb]).find('.difference').length)
            --col_nmb;
        a = $(atds[col_nmb]);
        b = $(btds[col_nmb]);
        a = getText(a);
        b = getText(b);
        if (!isNaN(parseFloat(a))) {
            a = parseFloat(a);
            b = parseFloat(b);
            return neg((a < b) ? -1 : (a > b) ? 1 : 0);
        }
        else {
            return neg(a.localeCompare(b, 'pl'));
        }
    });
    parent.append(upd);
};

var prepare = function(tdid) {
        var $head = $('#'+ tdid +' thead tr td').filter(function () {
            return $(this).prop('colspan') == 1
        });
        var ord = [0, 1, 2, 5, 3, 4, 6, 7].reverse();
        $head.each(function (i) {
                var numb = ord.pop();
                $this = $(this);
                var targ = $($this.find('div')[0]);
                $this.on('click', function () {
                    // close details box in list of municipalities
                    $('.muni_details_row').remove();
                    $('.clicked_row').removeClass('clicked_row');

                    $(this.parentNode.parentNode).find('.clicked').removeClass('clicked');
                    targ.addClass('clicked');
                    sort(tdid, numb, targ.toggleClass('asc').hasClass('asc'));
                    $('.asc:not(.clicked)').removeClass();
                });
                $this.css('cursor', 'pointer');
            }
        );
    }

$(document).ready( function() {
    prepare('main_comparison');
    prepare('detailed');
});