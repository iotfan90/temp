/**
 * Created by Yuki on 7/22/16.
 */
angular.module('modjento').controller('CustomerEmailController', [ '$scope','$window', function($scope, $window) {
    $scope.submitEmail = function () {
        var email = $scope.email;
        $window.location.href = "http://" + $window.location.host + "/api/customer-dashboard/?email=" + email;
    }
}]);

