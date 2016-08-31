google.charts.load('current', {'packages': ['geochart']});

function drawMarkersMap(c1, c2) {
    var $loader = $('#map_loader');
    $loader.css('display', 'block');
    content = [['Province', 'first_cand_per', {role: 'tooltip', p:{html:true}}]];
    $main_comp = $('#main_comparison tbody').children('tr').each(function(nr, obj) {
        var obj = $(obj);
        var tds = obj.children();
        var fst = parseInt(tds[3].innerText);
        var snd = parseInt(tds[6].innerText);
        var desc = c1 + ": <br>" + fst + "<br>" + c2 + ": <br>" + snd;
        content.push([{v:obj.find('.voiv_code').prop('id').split('_')[1], f:tds[1].innerText}, fst/(fst+snd), desc]);
    });
    var data = google.visualization.arrayToDataTable(content);
    var options = {
        region: 'PL',
        resolution: 'provinces',
        backgroundColor: '#ddd',
        legend: 'none',
        colorAxis: {colors: ['#fa8309', '#0260d4']},
        tooltip: {isHtml: true}
    };
    var $mapdiv = $('#results_map');
    var $map_container = $('<div></div>');
    var outer_height = $mapdiv.height();
    var outer_width = $mapdiv.width();
    var scale = 1.5;
    var pos = $loader.position();
    $loader.css({ position: "absolute",
        marginLeft: $loader.css('margin-left'),
        marginTop: $loader.css('margin-top'),
        top: pos.top, left: pos.left });
    $mapdiv.append($map_container);
    $map_container.css({
        'height': outer_height * scale,
        'width': outer_width * scale,
        'position': 'relative',
        'top': (1 - scale) * outer_height / 2,
        'left': (1 - scale) * outer_width / 2
    });
    var scaleMap = function() {
        $loader.css('display', 'none');
    };
    var chart = new google.visualization.GeoChart($map_container[0]);
    google.visualization.events.addListener(chart, 'ready', scaleMap);
    google.visualization.events.addListener(chart, 'regionClick', function (reg) {
        detail('voiv', reg.region);
    });
    chart.draw(data, options);
};
