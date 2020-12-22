/**
 * Created by Yuki on 4/18/16.
 */
angular.module('modjento').controller('EmailSignUpTrackController', [ '$scope', function($scope) {

    /**
     * Create chart to show email_signups over time
     **/

    $scope.trackRows = window.emailTrackData.tracks;
    $scope.chartLabels = $scope.trackRows.map(function (x) {
        return x.day;
    });
    var line1 = $scope.trackRows.map(function(x) {
        return x.new_email;
    });
    var line2 = $scope.trackRows.map(function(x) {
        return x.unsubscribes;
    });
    $scope.chartSeries = [ 'Subscribes', 'Unsubscribes' ];
    $scope.chartData = [
        line1,
        line2
    ];
    $scope.chartColours = [ '#b565a7', '#dcb5b4' ];
    $scope.chartOptions = {
        scaleOverride: true,
        scaleStartValue: 0,
        scaleSteps: 10,
        scaleStepWidth: 400,
        datasetFill: false,
        scaleLabel: function (payload) {
            return payload.value;
        },
    };
}]);

