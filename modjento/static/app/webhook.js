angular.module('modjento').controller('WebhookController', [ '$scope', '$http', function ($scope, $http) {
    $scope.stores = window.shopify_data.stores;
    $scope.topics = window.shopify_data.topics;
    $scope.selectedStore = $scope.stores[0]
    $scope.selectedTopic = $scope.topics[0]
    $scope.getEndpoint = window.shopify_data.getEndpoint;
    $scope.createEndpoint = window.shopify_data.createEndpoint;
    $scope.deleteEndpoint = window.shopify_data.deleteEndpoint;
    $scope.webhooks = [];
    $scope.finished = false;

    $scope.selectStore = function () {
        $scope.finished = false;
        $scope.loading = true;
        var fd = new FormData();
        fd.append('store', $scope.selectedStore.id);
        $http.post($scope.getEndpoint, fd, {headers:{'Content-Type': undefined}}).then(function (response) {
            $scope.loading = false;
            $scope.finished = true;

            var data = response.data;
            if(data.success){
                $scope.webhooks = JSON.parse(data.webhooks);
            }else{
                $scope.errorMessage = data.message || null;
            }
            $scope.success = data.success;
        });
    }

    $scope.registerWebhook = function(){
        $scope.clearMessages();
        $scope.loadingRegisterWebhook = true;
        var fd = new FormData();
        fd.append('store', $scope.selectedStore.id);
        fd.append('topic', $scope.selectedTopic);
        fd.append('address', $scope.address);
        $http.post($scope.createEndpoint, fd, {headers:{'Content-Type': undefined}}).then(function (response) {
            $scope.loadingRegisterWebhook = false;
            var data = response.data;
            if(data.success){
                document.getElementById('modal-dismiss').click();
                $scope.successMessage = 'Webhook successfully registered.';
                $scope.selectStore();
            }else{
                $scope.registrationMessage = data.message || null;
            }
        });
    };

    $scope.deleteWebhook = function (webhook) {
        webhook.deleting = true;
        $scope.clearMessages();
        var fd = new FormData();
        fd.append('store', $scope.selectedStore.id);
        fd.append('webhook_id', webhook.id);
        $http.post($scope.deleteEndpoint, fd, {headers:{'Content-Type': undefined}}).then(function (response) {
            webhook.deleting = false;
            var data = response.data;
            if(data.success){
                $scope.selectStore();
                $scope.successMessage = 'Webhook successfully deleted.';
            }else{
                $scope.errorMessage = data.message || null;
            }
        });
    };

    $scope.clearMessages = function () {
        $scope.errorMessage = null;
        $scope.successMessage = null;
        $scope.registrationMessage = null;
    }

    var init = function () {
        $scope.selectStore();
    };
    init();
}]);
