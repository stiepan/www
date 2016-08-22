google.charts.load('current', {'packages': ['geochart']});
google.charts.setOnLoadCallback(drawMarkersMap);

function drawMarkersMap() {
    content = [['Province', 'first_cand_per', {role: 'tooltip', p:{html:true}}]];
    $main_comp = $('#main_comparison').find('tbody').children('tr').each(function(nr, obj) {
        var obj = $(obj);
        var tds = obj.children();
        var fst = parseInt(tds[3].innerText);
        var snd = parseInt(tds[6].innerText);
        var desc = $('#cand_name_0').text() + ": <br>" + fst + "<br>" + $('#cand_name_1').text() + ": <br>" + snd;
        content.push([{v:obj.find('.voiv_code').text(), f:tds[1].innerText}, fst/(fst+snd), desc]);
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
    var $loader = $('#map_loader');
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
        $('#map_loader').css('display', 'none');
    };
    var chart = new google.visualization.GeoChart($map_container[0]);
    google.visualization.events.addListener(chart, 'ready', scaleMap);
    chart.draw(data, options);
};
