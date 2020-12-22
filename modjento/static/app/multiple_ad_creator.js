angular.module('modjento').controller('FacebookMultipleAdCreatorController', [ '$scope', function($scope) {
    $scope.uploadFile = function () {
        $scope.loading = true;
        $("#uploadFileForm").submit();
    }
}])
.directive('validFile',function(){
    return {
        require:'ngModel',
        link:function(scope,el,attrs,ctrl){
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
});
