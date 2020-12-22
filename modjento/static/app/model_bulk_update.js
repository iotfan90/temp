angular.module('modjento').controller('ModelsBulkUpdateController', [ '$scope', '$http', function ($scope, $http) {
    $scope.uploadEndpoint = window.shopify_data.uploadEndpoint;
    $scope.non_processed_models = [];
    $scope.processed_models_counter = 0;

    $scope.uploadFile = function () {
        $scope.finished = false;
        var file = $scope.myFile;
        var fd = new FormData();
        fd.append('file', file);
        $scope.loading = true;
        $http.post($scope.uploadEndpoint, fd, {headers:{'Content-Type': undefined}}).then(function (response) {
            $scope.loading = false;
            $scope.finished = true;

            var data = response.data;
            if(data.success){
                $scope.processed_models_counter = data.processed_models_counter;
                $scope.non_processed_models = JSON.parse(data.non_processed_models);
            }else{
                $scope.message = data.message || null;
            }
            $scope.success = data.success;


        });
    }
}])
.directive('validFile',function(){
    return {
        require:'ngModel',
        link:function(scope, el, attrs, ctrl){
            ctrl.$setValidity('validFile', el.val() != '');
            //change event is fired when file is selected
            el.bind('change',function(){
                ctrl.$setValidity('validFile', el.val() != '');
                scope.$apply(function(){
                    ctrl.$setViewValue(el.val());
                    ctrl.$render();
                });
            });
        }
    }
})
.directive('fileModel', ['$parse', function ($parse) {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            var model = $parse(attrs.fileModel);
            var modelSetter = model.assign;

            element.bind('change', function(){
                scope.$apply(function(){
                    modelSetter(scope, element[0].files[0]);
                });
            });
        }
    };
}]);
