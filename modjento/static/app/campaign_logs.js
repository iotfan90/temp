angular.module('modjento').controller('LifecycleCampaignLogsController', [ '$scope', function($scope) {
    $scope.logs = window.lifecycle_data.logs;
    $scope.pageData = window.lifecycle_data.page_data;
    $scope.prev = $scope.pageData.current - 1;
    $scope.nxt = $scope.pageData.current + 1;
    $scope.pageData['previous_page'] = $scope.pageData.previous ? ('?page=' + $scope.prev) : '#';
    $scope.pageData['next_page'] = $scope.pageData.next ? ('?page='+$scope.nxt) : '#';

}]);
