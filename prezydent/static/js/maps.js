google.charts.load('current', {'packages': ['geochart']});
google.charts.setOnLoadCallback(drawMarkersMap);

function drawMarkersMap() {
    var data = google.visualization.arrayToDataTable([
        ['Province', '{{ first_name }}', '{{ second_name }}', {role: 'tooltip', p:{html:true}}],
        [{v: 'PL-MZ', f:'mazowieckie'}, 80, 20, 'kek'],
        ['PL-MA', 99, 10, 'zal'],
        ['PL-DS', 59, 49, 'zal']
    ]);
    var options = {
        region: 'PL',
        resolution: 'provinces',
        backgroundColor: '#ddd',
        legend: 'none',
        colorAxis: {colors: ['#0260d4', '#fa8309']},
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
