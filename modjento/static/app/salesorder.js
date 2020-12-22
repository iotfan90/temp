/**
 * Created by Yuki on 4/18/16.
 */
angular.module('modjento').controller('SalesOrderController', [ '$scope', '$http', '$location', function($scope, $http, $location) {
    $scope.currentSort = window.currentSort;
    $scope.refreshReportEndpoint = window.refreshReportEndpoint;

    function initializeProducts(products, pageData) {
        $scope.pageData = pageData;
        $scope.currentPage = $scope.pageData.page;
        $scope.pages = $scope.pageData.pages;
        $scope.refreshReportProcessing = false;
        $scope.refreshReportFinished = false;
        $scope.refreshReportSuccess = false;
        $scope.refreshReportMessage = null;
    }

    (function initializeInputs() {
        var queryString = location.search;
        var params = decodeUrl(queryString);
        if (params.searchField !== undefined) {
            var searchMap = JSON.parse(params.searchField);
            $scope.searchPid = searchMap.product_id;
            $scope.searchSku = searchMap.sku;
            // $scope.searchName = searchMap.name;
        }
    })();

    /**
     * Initial page load
     */
    initializeProducts(salesReportData.products, salesReportData.pageProducts);

    $scope.addSort = function (newSort) {
        switch ($scope.currentSort.indexOf(newSort)) {
            case 1:
                $scope.currentSort = newSort;
                break;
            default:
                $scope.currentSort = '-' + newSort;
        }
        var queryString = location.search;

        var params = decodeUrl(queryString);
        params.sort = $scope.currentSort;
        encodeUrl(queryString, params);
    };

    $scope.search = function () {
        var searchMap = {};
        searchMap['product_id'] = $scope.searchPid;
        searchMap['sku'] = $scope.searchSku;
        // searchMap['name'] = $scope.searchName;
        var queryString = location.search;
        var params = decodeUrl(queryString);
        params.searchField = JSON.stringify(searchMap);
        encodeUrl(queryString, params);
    };

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
        return params;
    }

    $scope.refreshReport = function () {
        $scope.refreshReportProcessing = true;

        $http.post($scope.refreshReportEndpoint, null).then(function (response) {
            if (response.status == 200 && response.data.success) {
                $scope.refreshReportSuccess = true;
                $scope.refreshReportMessage = response.data.message;
            }else{
                $scope.refreshReportSuccess = false;
                $scope.refreshReportMessage = response.data.message;
            }
            $scope.refreshReportProcessing = false;
            $scope.refreshReportFinished = true;
        });
    };
}]);

