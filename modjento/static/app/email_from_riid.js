angular.module('modjento').controller('EmailFromRIID', [ '$scope', '$http', function($scope, $http) {
    $scope.getEmailEndpoint = window.modjento_data.emailFromRiidEndpoint;
    function getEmail() {
        $scope.loading = 'Uploading image';
        $http.post($scope.getEmailEndpoint, $scope.riid).then(function (response) {
            console.log(response);
            $scope.loading = false;
            var data = response.data;
            var email = response.email;
            $scope.finished = true;
            console.log(response);
            $scope.message = email;
        });
    }

    $scope.getEmail = function() {
        getEmail();
    }

}]);
