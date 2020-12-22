/**
 * Created by Yuki on 8/23/16.
 */
angular.module('modjento').controller('ProductReviewController', [ '$scope', '$http', function($scope, $http) {
    console.log(window.product_review_data);
    $scope.stars = window.product_review_data.stars;
    $scope.star1 = $scope.stars[0];
    $scope.star2 = $scope.stars[1];
    $scope.star3 = $scope.stars[2];
    $scope.star4 = $scope.stars[3];
    $scope.star5 = $scope.stars[4];
    $scope.email = window.product_review_data.email;
    $scope.product = window.product_review_data.product;
    $scope.showReview = ($scope.product != undefined && Object.keys($scope.product).length > 0);
    $scope.order_id = window.product_review_data.order_id;
    $scope.riid = window.product_review_data.riid;
    $scope.strands_products1 = window.product_review_data.strands_products.slice(0,3);
    $scope.strands_products2 = window.product_review_data.strands_products.slice(3,6);
    console.log($scope.strands_products1);
    $scope.authenticated = window.product_review_data.authenticated;
    function initializePage() {
        if ($scope.authenticated == undefined || $scope.authenticated == false) {
            document.getElementById("bs-navbar-collapse-1").style.visibility = "hidden";
            document.getElementById("footer").style.visibility = "hidden";
            document.getElementById("bs-navbar-collapse-0").style.visibility = "hidden";
        }

    }
    initializePage();

}]);
