/**
 * Created by Yuki on 7/26/16.
 */
angular.module('modjento').controller('OrderLookupController', [ '$scope', '$location','$http', '$window', function($scope, $location, $http, $window) {
    $scope.resetData = function () {
        $scope.increment_id = '';
        $scope.customer_email = '';
        $scope.firstname = '';
        $scope.lastname = '';
        $scope.datefrom = '';
        $scope.dateto = '';
        $scope.postcode = '';
        $scope.telephone = '';
        $scope.lastfour = '';
    };

    function initializeOrders(pageData) {
        $scope.pageData = pageData;
        $scope.currentPage = $scope.pageData.page;
        $scope.pages = $scope.pageData.pages;

    }
    initializeOrders(window.orderLookup.page_orders);


    $scope.orders = window.orderLookup.orders;

    function decodeUrl(queryString) {
        if (queryString.length) {
            var params = queryString.substring(1).split('&').map(function (x) {
                return x.split('=').map(decodeURIComponent);
            }).reduce(function (result, value) {
                result[value[0]] = value[1];
                return result;
            }, {});
        }
        else {
            params = {};
        }
        return params
    }

    function encodeUrl(queryString, params) {
        var newQueryString = Object.keys(params).map(function (x) {
            return [ encodeURIComponent(x), encodeURIComponent(params[x])].join('=');
        }).join('&');
        var url = $location.absUrl();
        if (queryString.length) {
            url = url.substring(0, url.indexOf('?'));
        }
        window.location.href = url + '?' + newQueryString;
    }

    $scope.submitData = function () {
        var queryString = location.search;
        var params = decodeUrl(queryString);

        if ($scope.increment_id) {
            params.increment_id = $scope.increment_id;
        } else{
            delete params.increment_id;
        }
        if ($scope.customer_email) {
            params.customer_email = JSON.stringify($scope.customer_email);
        } else{
            delete params.customer_email;
        }
        if ($scope.firstname) {
            params.customer_firstname = JSON.stringify($scope.firstname);
        } else {
            delete params.customer_firstname;
        }
        if ($scope.lastname) {
            params.customer_lastname = JSON.stringify($scope.lastname);
        } else {
            delete params.customer_lastname;
        }

        if ($scope.datefrom) {
            params.datefrom = JSON.stringify($scope.datefrom);
        } else{
            delete params.datefrom;
        }
        if ($scope.dateto) {
            params.dateto = JSON.stringify($scope.dateto);
        } else{
            delete params.dateto;
        }
        if ($scope.postcode) {
            params.postcode = JSON.stringify($scope.postcode);
        } else {
            delete params.postcode;
        }
        if ($scope.telephone) {
            params.telephone = JSON.stringify($scope.telephone);
        } else {
            delete params.telephone;
        }
        if ($scope.lastfour) {
            params.lastfour = JSON.stringify($scope.lastfour);
        } else {
            delete params.lastfour;
        }
        encodeUrl(queryString, params);

    };

    (function initializeInputs() {
        var queryString = location.search;
        var params = decodeUrl(queryString);
        $scope.increment_id = params.increment_id || null;
        $scope.customer_email = normalizeInout(params.customer_email);
        $scope.firstname = normalizeInout(params.customer_firstname);
        $scope.lastname = normalizeInout(params.customer_lastname);
        $scope.datefrom = new Date(normalizeInout(params.datefrom));
        $scope.dateto = new Date(normalizeInout(params.dateto));
        $scope.telephone = normalizeInout(params.telephone);
        $scope.postcode = normalizeInout(params.postcode);
        $scope.lastfour = normalizeInout(params.lastfour);
        $scope.showTable = queryString.length > 0;
    })();
    $scope.orderDetailsEndpoint = window.orderLookup.orderDetailEndpoint;

    function normalizeInout(fieldParam) {
        if (fieldParam != undefined && fieldParam.length > 0) {
            fieldParam = fieldParam.substring(1, fieldParam.length - 1);
        } else {
            fieldParam = undefined;
        }
        return fieldParam;
    }
    $scope.goToPage = function (p) {
        var queryString = location.search;
        var params = decodeUrl(queryString);
        if (p != $scope.pageData.current) {
            params.page = p;
            encodeUrl(queryString, params);
        }

    };

    $scope.goToDetail = function (orderNum, orderEmail) {
        var url = "http://" + $window.location.host + "/api/order_details/";
        var separator = (url.indexOf('?') > -1) ? "&" : "?";
        var qs1 = "orderNum=" + encodeURIComponent(orderNum);
        var qs2 = "orderEmail=" + encodeURIComponent(orderEmail);
        $window.location.href = url + separator + qs1 + '&' + qs2;
    }

}]);
