angular.module('modjento').controller('SmartCollectionSyncController', [ '$scope', '$http', '$timeout', function ($scope, $http, $timeout) {
    $scope.collections = window.shopify_data.collections;
    $scope.smart_collections_upload_endpoint = window.smart_collections_upload_endpoint;
    $scope.smart_collections_sync_endpoint = window.smart_collections_sync_endpoint;
    $scope.upload_counter = 0;

    $scope.uploadCollection = function (collection) {
        if(!collection.success){
            collection.uploading = true;
            $http.post($scope.smart_collections_upload_endpoint, collection).then(function (response) {
                collection.uploading = false;
                collection.uploaded = true;
                collection.success = response.data.success;
                collection.message = response.data.message;
                if(collection.success)
                    $scope.upload_counter += 1;
            });
        }
    };


    $scope.uploadAllCollection = function () {
        $scope.uploadingAllCollection = true;
        var loop = 0;

        var looper = function(){
            if (loop < $scope.collections.length) {
                var collection = $scope.collections[loop];
                $scope.uploadCollection(collection);
                loop++;
            } else {
                $scope.uploadingAllCollection = false;
                return;
            }
            setTimeout(looper, 600);
        };

        looper();
    };

    $scope.syncSmartCollections = function () {
        $scope.loadingSyncSmartCollections = true;
        $scope.syncSmartCollectionsResponse = null;
        $http.post($scope.smart_collections_sync_endpoint, {}).then(function (response) {
            $scope.loadingSyncSmartCollections = false;
            var data = response.data;
            $scope.syncSmartCollectionsResponse = {
                'success': data.success,
                'message': data.message
            }
            if(data.success){
                $scope.syncSmartCollectionsResponse = {
                    'success': data.success,
                    'message': data.message + '. Please, REFRESH the page.'
                }
                setTimeout(function () { location.reload(true); }, 3000);
            }else{
                $scope.syncSmartCollectionsResponse = {
                    'success': data.success,
                    'message': data.message
                }
            }
        });
    };

}]);

