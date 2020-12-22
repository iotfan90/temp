modjentoApp.controller('KpiController', [ '$scope', function ($scope) {
    var chartData = dice_data.chartData;
    if (chartData[0].period === 'Total') chartData = chartData.slice(1);
    chartData.reverse();
    $scope.chartLabels = chartData.map(function (x) {
        return x.period;
    });
    $scope.chartSeries = [ 'Net Sales', 'Total Orders' ];
    $scope.chartData = [
        chartData.map(function (x) { return x.net_sales; }),
        chartData.map(function (x) { return x.total_orders; })
    ];
    $scope.chartOptions = {
        scaleLabel: function (payload) {
            return Number(payload.value).toLocaleString(undefined, { style: 'currency', currency: 'usd' });
        },
        multiTooltipTemplate: function (payload) {
            if (payload.datasetLabel === 'Net Sales') {
                return payload.datasetLabel + ': ' + Number(payload.value).toLocaleString(undefined, {style: 'currency', currency: 'usd'});
            }
            return payload.datasetLabel + ': ' + Number(payload.value).toLocaleString();
        }
    };
} ]);

modjentoApp.controller('KpiHourlyController', [ '$scope', function ($scope) {
    var grossSales = modjento_data.grossSales;
    var estimated = grossSales.reduce(function (result, value) {
        result[value.period] = !!value.estimated;
        return result;
    }, {});
    grossSales.reverse();
    grossSales = grossSales.slice(1);
    var line1 = grossSales.slice(0, 16);
    var line2 = grossSales.slice(24, 40);
    line1.reverse();
    line2.reverse();
    $scope.chartLabels = line1.map(function (x) {
        return x.period;
    });
    $scope.chartSeries = [ 'Today', 'Yesterday' ];
    $scope.chartData = [
        line1.map(function (x) { return x.conversion_rate; }),
        line2.map(function (x) { return x.conversion_rate; })
    ];
    $scope.chartColours = [ '#b565a7', '#dcb5b4' ];
    $scope.chartOptions = {
        scaleOverride: true,
        scaleStartValue: 0,
        scaleSteps: 8,
        scaleStepWidth: 1,
        datasetFill: false,
        scaleLabel: function (payload) {
            return payload.value + '%';
        },
        multiTooltipTemplate: function (payload) {
            if (payload.datasetLabel === 'Today') {
                return payload.datasetLabel + ': '
                    + Number(payload.value).toLocaleString(
                        undefined, {maximumFractionDigits: 2})
                    + '%' + (estimated[payload.label] ? '*' : '');
            }
            return payload.datasetLabel + ': '
                + Number(payload.value).toLocaleString(
                    undefined, {maximumFractionDigits: 2})
                + '%';
        }
    };
} ]);
