angular.module('modjento').controller('FacebookMultipleAdPreviewController', [ '$scope', function($scope) {
    $scope.facebook_ads = window.modjento_data.facebook_ads;
    $scope.facebookUploadEndpoint = window.modjento_data.facebookUploadEndpoint;
}]);
