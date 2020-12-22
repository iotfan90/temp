/**
 * Created by Yuki on 8/8/16.
 */
angular.module('modjento').controller('UnsubForm', [ '$scope', function($scope) {
    $scope.authenticated = window.modjento_data.authenticated;
    function initializePage() {
        console.log('initialize=%s',$scope.authenticated);
        if ($scope.authenticated == undefined || $scope.authenticated == false) {
            document.getElementById("bs-navbar-collapse-1").style.visibility = "hidden";
            document.getElementById("footer").style.visibility = "hidden";
        }

    }
    initializePage();

    $scope.submitPreference = function () {
        $("#ubsubForm").submit();
        console.log('submit=%s',$scope.authenticated);
        if ($scope.authenticated == undefined || $scope.authenticated == false) {
            document.getElementById("bs-navbar-collapse-1").style.visibility = "hidden";
            document.getElementById("footer").style.visibility = "hidden";
        }
    };


}]);
