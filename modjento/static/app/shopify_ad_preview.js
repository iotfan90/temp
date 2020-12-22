angular.module('modjento').controller('FacebookShopifyAdPreviewController', [ '$scope', '$http', '$timeout', function ($scope, $http, $timeout) {
    $scope.imageUploadEndpoint = window.modjento_data.imageUploadEndpoint;
    $scope.adUploadEndpoint = window.modjento_data.adUploadEndpoint;
    $scope.loading = false;
    $scope.finished = false;
    $scope.success = null;
    $scope.message = null;
    $scope.adData = {
        campaign_id: window.modjento_data.campaignId,
        campaign_name: window.modjento_data.campaignName,
        ad_set_id: window.modjento_data.adSetId,
        is_active: false,
        handle_url: window.modjento_data.handleUrl,
        name: window.modjento_data.ad_name,
        message: window.modjento_data.ad_message,
        fb_credentials: window.modjento_data.fb_credentials,
        products: window.modjento_data.products.map(function (x) {
            x.selectedImage = 0;
            x.add_banner = false;
            x.add_shop_now = false;
            x.show_stars = false;
            x.fb_credentials = window.modjento_data.fb_credentials;
            return x;
        }),
        ad_set_name: window.modjento_data.adSetName,
        handle: window.modjento_data.handle,
    };

    $timeout(function () {
        $('.card-text').each(function (_, x) {
            x = $(x);
            var n = x.data('index');
            x.slick({
                infinite: true,
                slidesToShow: 1,
                dots: true,
                slidesToScroll: 1
            }).on('afterChange', function (event, slick, currentSlide) {
                $scope.$apply(function () {
                    $scope.adData.products[n].selectedImage = currentSlide;
                });
            });
        });
    }, 100, false);


    function updateTracking (tracking, adName) {
        var linkList = tracking.split('&utm_source');
        return [linkList[0], adName, '&utm_source', linkList[1]].join('');
    }

    $scope.updateHandle = function() {
        $scope.adData.handle_url = updateTracking(window.modjento_data.handleUrl, $scope.adData.name);
    };

    function updateProductLink() {
        for(var i=0; i<$scope.adData.products.length; i++) {
            $scope.adData.products[i].link=updateTracking($scope.adData.products[i].link, $scope.adData.name)
        }
    }

    function uploadAd(counter) {
        var max_retries = 10;
        updateProductLink();
        console.log($scope.adData);
        $http.post($scope.adUploadEndpoint, $scope.adData).then(function (response) {
            $scope.finished = true;
            var data = response.data;
            if(!data.success && counter < max_retries){
                uploadAd(++counter);
                $scope.message = 'Upload Ad failed - Retry: #' + counter;
                $scope.success = false;
            }else{
                $scope.loading = false;
                $scope.success = data.success;
                $scope.message = data.message || null;
            }
        });
    }

    function uploadImage(n) {
        if (n == $scope.adData.products.length) {
            $scope.loading = 'Uploading Ad';
            uploadAd(0);
            return;
        }
        var x = $scope.adData.products[n];

        x.image = x.images[x.selectedImage];
        x.loading = 'Uploading image';
        $scope.loading = 'Uploading image [' + x.image + ']';
        $http.post($scope.imageUploadEndpoint, x).then(function (response) {
            x.loading = false;
            if (response.status == 200 && response.data.success) {
                x.image_hash = response.data.image_hash;
            }
            uploadImage(n + 1);
        });
    }

    $scope.uploadAd = function () {
        $scope.submitted = true;
        $scope.finished = false;
        if ($scope.adData.name) {
            uploadImage(0);
        }
    };
}]);
