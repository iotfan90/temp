/**
 * Created by Yuki on 9/12/16.
 */
angular.module('modjento').controller('BdaySubmission', [ '$scope', '$http', function($scope, $http) {
    $scope.authenticated = window.bdayData.authenticated;
    $scope.frequencyOptions = window.bdayData.frequencyOptions;
    $scope.email = window.bdayData.email;
    $scope.deviceBrands = window.bdayData.deviceBrands;
    $scope.mp_brand_models = window.bdayData.mp_brand_models;
    $scope.riid = window.bdayData.riid;
    $scope.mp_model_id = window.bdayData.mp_model_id;
    $scope.updateModels = function () {
      $scope.models = $scope.mp_brand_models[$scope.selectedBrand];
    };
    $scope.updateModelId = function () {
      $scope.modelId = $scope.mp_model_id[$scope.selectedModel];
    };
    $scope.emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/i;

    // console.log(selectedColor);

    $scope.colors = [
        {label: 'Red', value: '#FF0000'},
        {label: 'Orange', value: '#FFA500'},
        {label: 'Yellow', value: '#ffff00'},
        {label: 'Green', value: '#008000'},
        {label: 'Blue', value: '#0000FF'},
        {label: 'Purple', value: '#800080'},
        {label: 'Gold', value: '#D4AF37'},
        {label: 'Silver', value: '#C0C0C0'},
        {label: 'White', value: '#ffffff'},
        {label: 'Black', value: '#000000'}
    ];

    function initializePage() {
        console.log('initialize=%s',$scope.authenticated);
        if ($scope.authenticated == undefined || $scope.authenticated == false) {
            document.getElementById("bs-navbar-collapse-1").style.visibility = "hidden";
            document.getElementById("footer").style.visibility = "hidden";
            document.getElementById("bs-navbar-collapse-0").style.visibility = "hidden";
        }
        $scope.selectedBrand = null;
        $scope.selectedModel = null;

    }
    initializePage();

}]);
