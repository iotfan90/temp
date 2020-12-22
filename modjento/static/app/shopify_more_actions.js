angular.module('modjento').controller('ShopifyMoreActionsController', [ '$scope', '$http', function ($scope, $http) {
    $scope.products_sync_endpoint = window.products_sync_endpoint;
    $scope.smart_collections_sync_endpoint = window.smart_collections_sync_endpoint;
    $scope.we_feed_generation_endpoint = window.we_feed_generation_endpoint;
    $scope.upload_brand_model_js_endpoint = window.upload_brand_model_js_endpoint;
    $scope.update_smart_collections_shopify_endpoint = window.update_smart_collections_shopify_endpoint;
    $scope.orders_sync_endpoint = window.orders_sync_endpoint;

    $scope.syncProducts = function () {
        $scope.loadingSyncProducts = true;
        $scope.syncProductsResponse = null;
        $http.post($scope.products_sync_endpoint, {}).then(function (response) {
            $scope.loadingSyncProducts = false;
            $scope.syncProductsResponse = {
                'success': response.data.success,
                'message': response.data.message
            }
        });
    };
    $scope.syncSmartCollections = function () {
        $scope.loadingSyncSmartCollections = true;
        $scope.syncSmartCollectionsResponse = null;
        $http.post($scope.smart_collections_sync_endpoint, {}).then(function (response) {
            $scope.loadingSyncSmartCollections = false;
            $scope.syncSmartCollectionsResponse = {
                'success': response.data.success,
                'message': response.data.message
            }
        });
    };
    $scope.syncOrders = function () {
        $scope.loadingSyncOrders = true;
        $scope.syncOrdersResponse = null;
        $http.post($scope.orders_sync_endpoint, {}).then(function (response) {
            $scope.loadingSyncOrders = false;
            $scope.syncOrdersResponse = {
                'success': response.data.success,
                'message': response.data.message
            }
        });
    };

    $scope.generateWEProductFeeds = function () {
        $scope.loadingGenerateWEProductFeeds = true;
        $scope.generateWEProductFeedsResponse = null;
        $http.post($scope.we_feed_generation_endpoint, {}).then(function (response) {
            $scope.loadingGenerateWEProductFeeds = false;
            $scope.generateWEProductFeedsResponse = {
                'success': response.data.success,
                'message': response.data.message
            }
        });
    };
    $scope.uploadBrandModelJSFile = function () {
        $scope.loadingUploadBrandModelJSFile = true;
        $scope.uploadBrandModelJSFileResponse = null;
        $http.post($scope.upload_brand_model_js_endpoint, {}).then(function (response) {
            $scope.loadingUploadBrandModelJSFile = false;
            $scope.uploadBrandModelJSFileResponse = {
                'success': response.data.success,
                'message': response.data.message
            }
        });
    };
    $scope.updateSmartCollectionOnShopify = function () {
        $scope.loadingUpdateSmartCollectionOnShopify = true;
        $scope.uploadUpdateSmartCollectionOnShopifyResponse = null;
        $http.post($scope.update_smart_collections_shopify_endpoint, {}).then(function (response) {
            $scope.loadingUpdateSmartCollectionOnShopify = false;
            $scope.uploadUpdateSmartCollectionOnShopifyResponse = {
                'success': response.data.success,
                'message': response.data.message
            }
        });
    };

}]);

