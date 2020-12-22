/**
 * Created by Yuki on 6/24/16.
 */
angular.module('modjento').controller('PurchaseOrderController', [ '$scope', '$http', '$location', function($scope, $http, $location) {
    $scope.currentSort = window.currentSort;
    $scope.refreshReportEndpoint = window.refreshReportEndpoint;

    function initializeProducts(pageData) {
        $scope.pageData = pageData;
        console.log($scope.pageData);
        $scope.currentPage = $scope.pageData.page;
        $scope.pages = $scope.pageData.pages;
        $scope.checked = false;
        $scope.refreshReportProcessing = false;
        $scope.refreshReportFinished = false;
        $scope.refreshReportSuccess = false;
        $scope.refreshReportMessage = null;
    }
    /**
     * Initial page load
     */
    initializeProducts(poReportData.pageProducts);


    $scope.vendors = window.poReportData.vendors;

    (function initializeInputs() {
        // when the user searches by SKU, we have to parse out the
        // searchSkus from the query string to put them back into the
        // input field
        var queryString = location.search;
        var params = decodeUrl(queryString);
        if (params.searchSkus !== undefined) {
            $scope.searchSku = params.searchSkus;
        }
        if (params.vendor !== undefined) {
            $scope.selectedVendor = params.vendor;
        }
        if (params.leadTime !== undefined) {
            $scope.leadTime = params.leadTime;
        }else{
            $scope.leadTime = 7;
        }
        if (params.daysBetweenOrder !== undefined) {
            $scope.daysBetweenOrder = params.daysBetweenOrder;
        }else{
            $scope.daysBetweenOrder = 7;
        }
        if (params.serviceLevel !== undefined) {
            $scope.serviceLevel = params.serviceLevel;
        }else{
            $scope.serviceLevel = 0.8;
        }
        if (params.fb_discount !== undefined) {
            $scope.fb_DecayDiscount = params.fb_discount;
        }
        if (params.numOfDays !== undefined) {
            $scope.numOfDays = params.numOfDays;
        }
        if (params.checked !== undefined) {
            $scope.checked = params.checked === "true";
        }
        if (!$scope.selectedVendor && !$scope.searchSku) {
            $('#optionModal').modal('show');

        }
    })();

    $scope.selectedVendorChanged = function () {
        var queryString = location.search;
        var params = decodeUrl(queryString);
        params.vendor = $scope.selectedVendor;
        encodeUrl(queryString, params);

    };

    $scope.searchBySku = function (searchSku) {
        var queryString = location.search;
        var params = decodeUrl(queryString);
        params.searchSkus = searchSku;
        encodeUrl(queryString, params);
    };

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

    $scope.selectPage = function (p) {
        var queryString = location.search;
        var params = decodeUrl(queryString);
        if (p != $scope.pageData.current) {
            params.page = p;
        }
        encodeUrl(queryString, params);
    };
    $scope.firstPage = function () {
        var queryString = location.search;
        var params = decodeUrl(queryString);
        if ($scope.pageData.current != 1) {
            params.page = 1;
        }
        encodeUrl(queryString, params);
    };
    $scope.lastPage = function () {
        var queryString = location.search;
        var params = decodeUrl(queryString);
        if ($scope.pageData.current != $scope.pageData.last_page) {
            params.page = $scope.pageData.last_page;
        }
        encodeUrl(queryString, params);
    };

    // $scope.getLeadTime = function (leadTime) {
    //     var queryString = location.search;
    //     var params = decodeUrl(queryString);
    //     params.leadTime = leadTime;
    //     encodeUrl(queryString, params);
    // };

    // $scope.getNumOfDays = function (numOfDays) {
    //     var queryString = location.search;
    //     var params = decodeUrl(queryString);
    //     params.numOfDays = numOfDays;
    //     encodeUrl(queryString, params);
    // };

    // $scope.getFBDecay = function (fb_DecayDiscount) {
    //     var queryString = location.search;
    //     var params = decodeUrl(queryString);
    //     params.fb_discount = fb_DecayDiscount;
    //     encodeUrl(queryString, params);
    // };

    // $scope.getChecked = function () {
    //     var queryString = location.search;
    //     var params = decodeUrl(queryString);
    //     params.checked = $scope.checked;
    //     encodeUrl(queryString, params);
    // };

    $scope.submitData = function () {
        if (!$scope.selectedVendor && !$scope.searchSku) {
            $('#optionModal').modal('hide');
            return false;
        }
        var queryString = location.search;
        var params = decodeUrl(queryString);
        params.checked = $scope.checked;
        if (params.checked) {
            params.fb_discount = $scope.fb_DecayDiscount;
        } else {
            delete params.fb_discount;
        }
        if ($scope.numOfDays) {
            params.numOfDays = $scope.numOfDays;
        } else{
            delete params.numOfDays;
        }
        if ($scope.leadTime) {
            params.leadTime = $scope.leadTime;
        } else{
            delete params.leadTime;
        }
        if ($scope.daysBetweenOrder) {
            params.daysBetweenOrder = $scope.daysBetweenOrder;
        } else{
            delete params.daysBetweenOrder;
        }
        if ($scope.serviceLevel) {
            params.serviceLevel = $scope.serviceLevel;
        } else{
            delete params.serviceLevel;
        }
        if ($scope.searchSku && $scope.searchSku.length > 0) {
            console.log($scope.searchSku);
            params.searchSkus = $scope.searchSku;
        } else {
            delete params.searchSkus;
        }
        if ($scope.selectedVendor) {
            params.vendor = $scope.selectedVendor;
        }else{
            delete params.vendor;
        }
        encodeUrl(queryString, params);
    };

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

