angular.module('modjento').controller('ProductFeedExclusionUpdateController', [ '$scope', '$http', function ($scope, $http) {
    $scope.stores = window.shopify_data.stores;
    $scope.selectedStore = $scope.stores[0]
    $scope.uploadEndpoint = window.shopify_data.uploadEndpoint;
    $scope.non_processed_variants = [];
    $scope.processed_variants_counter = 0;

    $scope.uploadFile = function () {
        $scope.finished = false;
        var file = $scope.myFile;
        var fd = new FormData();
        fd.append('file', file);
        fd.append('store', $scope.selectedStore.id);
        $scope.loading = true;
        $http.post($scope.uploadEndpoint, fd, {headers:{'Content-Type': undefined}}).then(function (response) {
            $scope.loading = false;
            $scope.finished = true;

            var data = response.data;
            if(data.success){
                $scope.processed_variants_counter = data.processed_variants;
                $scope.non_processed_variants = JSON.parse(data.non_processed_variants);
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