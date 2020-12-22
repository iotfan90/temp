/**
 * Created by Yuki on 7/26/16.
 */
angular.module('modjento').controller('OrderDetailsController', [ '$scope', '$window', function($scope, $window) {

    $scope.orders = window.orderDetails.orders;
    console.log($scope.orders);
    $scope.recent_orders = window.orderDetails.recent_orders;
    $scope.helpscout = window.orderDetails.helpscout;
    $scope.coupons = window.orderDetails.coupons;
    $scope.email = window.orderDetails.email;
    $scope.customer_lifecycle = window.orderDetails.customer_lifecycle;
    $scope.conversations = window.orderDetails.conversations;
    console.log($scope.conversations);
    $scope.trackPageUrl = function(item) {
        if(item ==undefined || !item) {
            return;
        }
        var url = '';
        switch (item.carrier_code) {
            case 'fedex':
            case 'ground service':
                url = 'https://www.fedex.com/apps/fedextrack/?tracknumbers='
                    + item.track_number
                    + '&language=en&cntry_code=us';
                break;
            case 'usps':
                url = 'https://tools.usps.com/go/'
                    + 'TrackConfirmAction?qtc_tLabels1='
                    + item.track_number;
                break;
            case 'ups':
                url = 'https://wwwapps.ups.com/WebTracking/track'
                    + '?track=yes&trackNums='
                    + item.track_number;
                break;
            case 'flatrate_flatrate':
                url = 'https://tools.usps.com/go/'
                    + 'TrackConfirmAction?qtc_tLabels1='
                    + item.track_number;
                break;
        }
        return url;
    };

    $scope.goToOrderLookup = function (email) {
        email = JSON.stringify(email);
        $window.location.href = "http://" + $window.location.host + "/api/order_lookup/?customer_email=" + email;
    };

}]);
