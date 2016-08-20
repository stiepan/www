google.charts.load('current', {'packages': ['geochart']});
google.charts.setOnLoadCallback(drawMarkersMap);

function drawMarkersMap() {
    var data = google.visualization.arrayToDataTable([
        ['City', 'Population', 'Area'],
        ['Rome', 2761477, 1285.31],
        ['Milan', 1324110, 181.76],
        ['Naples', 959574, 117.27],
        ['Turin', 907563, 130.17],
        ['Palermo', 655875, 158.9],
        ['Genoa', 607906, 243.60],
        ['Bologna', 380181, 140.7],
        ['Florence', 371282, 102.41],
        ['Fiumicino', 67370, 213.44],
        ['Anzio', 52192, 43.43],
        ['Ciampino', 38262, 11]
    ]);
    var options = {
        region: 'PL',
        resolution: 'provinces',
        backgroundColor: '#ddd',
        enableRegionInteractivity: false,
        colorAxis: {colors: ['blue', 'orange']},
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
