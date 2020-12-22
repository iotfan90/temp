/**
 * Created by Yuki on 7/18/16.
 */
angular.module('modjento').controller('CustomerDashboardController', [ '$scope','$location', function($scope, $location) {
    function initializePage() {
        $scope.currentView = 0;
    }
    initializePage();
    $scope.orders = window.customerData.orders;
    $scope.sessions = window.customerData.sessions;
    $scope.pageviews = window.customerData.pageviews;
    $scope.email = window.customerData.email;
    $scope.orderSummary = window.customerData.order_summary;
    $scope.lifecycle = window.customerData.lifecycle;
    $scope.summaryLength = Object.keys($scope.orderSummary).length;
    $scope.changeView = function (currentView) {
        $scope.currentView = currentView;
    }
}]);

