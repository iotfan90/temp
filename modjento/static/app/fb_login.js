/**
 * Created by Yuki on 5/17/16.
 */
angular.module('modjento').controller('FacebookLoginController', [ '$scope','$http', function($scope, $http) {
    $scope.shortToken = '';
    $scope.loading = false;
    function statusChangeCallback(response) {
        if (response.status === 'connected') {
            $scope.loading = true;
            $scope.$apply(function () {
                $scope.shortToken = response.authResponse.accessToken;
                console.log(response.authResponse.accessToken);
                var token = {
                  'token': $scope.shortToken
                };
                $http.post('./', token).success(function () {
                    window.setTimeout(function(){
                        window.location.href = '/facebook/ad-creator';
                    }, 500);
                });
            });
            testAPI();
        } else if (response.status === 'not_authorized') {
          document.getElementById('status').innerHTML = 'Please type in the correct password';
        } else {
          document.getElementById('status').innerHTML = 'Please log ' +
            'into Facebook.';
        }


    }

    function checkLoginState() {
        FB.getLoginStatus(function(response) {
          statusChangeCallback(response);
        });
    }

    window.fbAsyncInit = function() {
        FB.init({
        appId      : window.facebook_app_id,
        cookie     : true,  // enable cookies to allow the server to access
        xfbml      : true,  // parse social plugins on this page
        version    : window.facebook_api_version
    });

    $scope.fbLogin = function() {

        FB.login(function(response) {
            statusChangeCallback(response)
        }, {scope: 'public_profile, email, ads_management, ads_read, manage_pages'});
    };



    FB.getLoginStatus(function(response) {
        statusChangeCallback(response);
        });
    };

    (function(d, s, id) {
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(id)) return;
    js = d.createElement(s); js.id = id;
    js.src = "//connect.facebook.net/en_US/sdk.js";
    fjs.parentNode.insertBefore(js, fjs);
    }(document, 'script', 'facebook-jssdk'));

    function testAPI() {
        console.log('Welcome!  Fetching your information.... ');
        FB.api('/me', function(response) {
          console.log('Successful login for: ' + response.name);
          document.getElementById('status').innerHTML =
            'Thanks for logging in, ' + response.name + '!';
        });
    }

}]);

