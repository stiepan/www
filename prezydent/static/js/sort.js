/**
 * Created by kamil on 22.08.16.
 */

var sort = function(col_nmb, asc) {
    var getText = function (el) {
        return el.contents().filter(function () {
            return this.nodeType == 3;
        })[0].nodeValue
    };
    var neg = (asc)? function(x){return x * (-1)} : function (x) {return x};
    var parent = $('#main_comparison tbody');
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

$(document).ready(
    function() {
        var $head = $('#main_comparison thead tr td').filter(function () {
            return $(this).prop('colspan') == 1
        });
        var ord = [0, 1, 2, 5, 3, 4, 6, 7].reverse();
        $head.each(function (i) {
                var numb = ord.pop();
                $this = $(this);
                var targ = $($this.find('div')[0]);
                $this.on('click', function () {
                    $(this.parentNode.parentNode).find('.clicked').removeClass('clicked');
                    targ.addClass('clicked');
                    sort(numb, targ.toggleClass('asc').hasClass('asc'));
                });
                $this.css('cursor', 'pointer');
            }
        );
    }
)