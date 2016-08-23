/**
 * Created by kamil on 22.08.16.
 */

var sort = function(col_nmb) {
    var $col = $('#main_comparison tbody tr td').filter(function(i){return i % 8 == col_nmb});
    $col.css('background', 'red');
};

$(document).ready(
    function() {
        var $head = $('#main_comparison thead tr td').filter(function() {return $(this).prop('colspan') == 1});
        var ord = [0, 1, 2, 5, 3, 4, 6, 7].reverse();
        $head.each(function(i) {
            var numb = ord.pop()
            $this = $(this);
            $this.on('click', function(){sort(numb)});
            $this.css('cursor', 'pointer');
        })
    }
);