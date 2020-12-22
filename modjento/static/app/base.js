"use strict";

var modjentoApp = angular.module('modjento', [ 'chart.js' ]);

modjentoApp.config(['$interpolateProvider', '$httpProvider', 'ChartJsProvider', function($interpolateProvider, $httpProvider, ChartJsProvider) {
    $interpolateProvider.startSymbol('[[').endSymbol(']]');

    /* Handle csrf requests in django */
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    ChartJsProvider.setOptions({
        scaleFontFamily: 'neuzeit, sans-serif',
        tooltipFontFamily: 'neuzeit, sans-serif',
        tooltipTitleFontFamily: 'freightsans, sans-serif',
        colours: [ '#b565a7', '#e1523d', '#009874', '#9baad1', '#f4c9c8', '#964f4c', '#b4acab', '#b08798', '#009874'  ]
        /*
        $serenity: #9baad1;
        $rose-quartz: #f4c9c8;
        $marsala: #964f4c;
        $ashes-of-roses: #b5acab;
        $orchid-haze: #b0879b;
        $radiant-orchid: #b565a7;
        $emerald: #009874;
        $tango-tangerine: #e1523d;
        */
    });
    //Chart.defaults.global.scaleFontFamily = 'neuzeit, sans-serif';
    //Chart.defaults.global.tooltipFontFamily = 'neuzeit, sans-serif';
    //Chart.defaults.global.tooltipTitleFontFamily = 'freightsans, sans-serif';
}]);
