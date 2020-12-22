angular.module('modjento').controller('LifecycleCampaignSelectController', [ '$scope', function($scope) {
    $scope.campaigns = window.lifecycle_data.campaigns;
}]);
