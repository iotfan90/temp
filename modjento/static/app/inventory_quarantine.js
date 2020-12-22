/**
 * Created by Yuki on 10/10/16.
 */
angular.module('modjento').controller('InventoryQuarantineController', [ '$scope', function($scope) {
    $scope.uploadFile = function () {
        $scope.loading = true;
        $("#uploadFileForm").submit();
    }

}]);


