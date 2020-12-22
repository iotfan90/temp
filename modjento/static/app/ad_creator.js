angular.module('modjento').controller('FacebookAdCreatorController', [ '$scope', function($scope) {
    $scope.campaigns = window.modjento_data.campaigns;
    $scope.all_ad_sets = window.modjento_data.ad_sets;
    var preferences = window.localStorage.getItem('FacebookAdCreator');
    if (preferences) {
        preferences = JSON.parse(preferences);
    }
    var mpCampaigns = $scope.campaigns.reduce(function (result, x) {
        result[x.campaign_id] = x;
        return result;
    }, {});
    var campaign_id = preferences && preferences.campaign_id || $scope.campaigns[0].campaign_id;
    if (!$scope.all_ad_sets[campaign_id]) {
        campaign_id = $scope.campaigns[0].campaign_id;
    }
    $scope.ad_sets = $scope.all_ad_sets[campaign_id];
    var ad_set_id = preferences && preferences.ad_set_id || $scope.ad_sets[0].ad_set_id;
    var ad_set_name = preferences && preferences.ad_set_name || $scope.ad_sets[0].name;
    var ad_set = $scope.ad_sets.filter(function (x) {
        return x.ad_set_id == ad_set_id;
    })[0] || null;
    var campaign = mpCampaigns[campaign_id];
    var campaign_name = preferences && preferences.campaign_name || null;
    $scope.data = {
        campaign: campaign,
        campaign_id: campaign_id,
        ad_set: ad_set,
        ad_set_id: ad_set_id,
        ad_set_name: ad_set_name,
        campaign_name: campaign_name,
        fb_credentials: window.modjento_data.fb_credentials,
    };

    $scope.savePreferences = function () {
        console.log('savePrefs');
        ad_set_id = $scope.data.ad_set['ad_set_id'];
        ad_set_name = $scope.data.ad_set['name'];
        preferences = $scope.data;
        preferences.ad_set_id = ad_set_id;
        preferences.ad_set_name = ad_set_name;
        window.localStorage.setItem('FacebookAdCreator', JSON.stringify(preferences));
    };


    $scope.submitData = function() {
        $("#frmProduct").submit();
    };

    $scope.updateAdSets = function () {
        $scope.data.campaign_id = $scope.data.campaign.campaign_id;
        $scope.data.campaign_name = $scope.data.campaign.name;
        $scope.ad_sets = $scope.all_ad_sets[$scope.data.campaign_id];
        $scope.data.ad_set = $scope.ad_sets[0];
        $scope.data.ad_set_id = $scope.data.ad_set.ad_set_id;
        $scope.data.ad_set_name = $scope.data.ad_set.name;
        $scope.savePreferences();
    };
}]);
