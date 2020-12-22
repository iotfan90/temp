/**
 * Created by Yuki on 10/31/16.
 */
angular.module('modjento').controller('ImageRetrievalViewController', [ '$scope', function($scope) {
    $scope.products = window.productImageData.products;
}]);
