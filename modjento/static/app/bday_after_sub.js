/**
 * Created by Yuki on 9/13/16.
 */
angular.module('modjento').controller('BDayAfter', [ '$scope', function($scope) {
    $scope.authenticated = window.bdaysubmitData.authenticated;
    function initializePage() {
        console.log('initialize=%s',$scope.authenticated);
        if ($scope.authenticated == undefined || $scope.authenticated == false) {
            document.getElementById("bs-navbar-collapse-1").style.visibility = "hidden";
            document.getElementById("footer").style.visibility = "hidden";
            document.getElementById("bs-navbar-collapse-0").style.visibility = "hidden";
        }

    }
    initializePage();

}]);
