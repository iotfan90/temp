/**
 * Created by Yuki on 7/18/16.
 */
angular.module('modjento').controller('LifecycleAnalyticsController', [ '$scope', function($scope) {
    $scope.sendersToday = window.senderData.senders_today;
    $scope.sendersYesterday = window.senderData.senders_yesterday;
    $scope.sendersWeek = window.senderData.senders_week;
    console.log($scope.sendersToday);
    // console.log($scope.sendersYesterday);
    // console.log($scope.sendersWeek);
    $scope.dateFrom = window.senderData.date_from;
    $scope.dateTo = window.senderData.date_to;
    $scope.chartLabels = $scope.sendersToday.map(function (x) {
        return x.hour;
    });
    $scope.chartSeries = [ 'Today', 'Yesterday', 'Week' ];
    $scope.chartData = [
        $scope.sendersToday.map(function(x) {return x.num;}),
        $scope.sendersYesterday.map(function(x) {return x.num;}),
        $scope.sendersWeek.map(function(x) {return x.num;})
    ];
    $scope.chartColours = [ '#b565a7', '#dcb5b4', '#00ADF9'];
    //scaleStepsWidth should be changed according to our daily nums of emails that were sent
    //here it is set to 1 for test in my local
    $scope.chartOptions = {
        scaleOverride: false,
        scaleStartValue: 0,
        scaleSteps: 30,
        scaleStepWidth: 200,
        datasetFill: false,
        scaleLabel: function (payload) {
            return payload.value;
        }
    };
}]);

