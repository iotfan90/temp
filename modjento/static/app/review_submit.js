/**
 * Created by Yuki on 9/1/16.
 */
angular.module('modjento').controller('ReviewSubmitController', [ '$scope', '$http', function($scope, $http) {
    $scope.authenticated = window.review_submit_data.authenticated;
    $scope.strands_products = window.review_submit_data.strands_products;
    $scope.strands_products1 = window.review_submit_data.strands_products.slice(0,3);
    $scope.strands_products2 = window.review_submit_data.strands_products.slice(3,6);
    function initializePage() {
        if ($scope.authenticated == undefined || $scope.authenticated == false) {
            document.getElementById("bs-navbar-collapse-1").style.visibility = "hidden";
            document.getElementById("footer").style.visibility = "hidden";
            document.getElementById("bs-navbar-collapse-0").style.visibility = "hidden";
        }

    }
    initializePage();

}]);
