/*
	MOBOVIDATA TRACKING JS
	By Kenny Smithnanic
*/


(function($) {
  function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName;

    for (var i = 0; i < sURLVariables.length; i++) {
      sParameterName = sURLVariables[i].split('=');
      if (sParameterName[0] === sParam)
        return sParameterName[1] === undefined ? true : sParameterName[1];
    }
    return false;
  }

  var mvCk = _satellite.readCookie('is_mobovida'),
      knCk = _satellite.readCookie('is_kenny'),
      isMobovida = !(mvCk == undefined || mvCk == 'undefined'),
      isKenny = !(knCk == undefined || knCk == 'undefined'),
      logging = false,
      isStaging = false;

  if (getUrlParameter['ik'] == 'y') {
    isKenny = true;
    console.log('Hi Kenny');
  }

  if (location.hostname.split('.')[0] == 'www') {
    logging = false;
  } else {
    isStaging = true;
    logging = true;
  }

  isStaging = true; // Forces isStaging always `true` -- negates above logic

  if (isStaging) {
    var testingDomain;
    if (_satellite.readCookie('is_kenny') == 'yes' || isKenny) {
      testingDomain = 'http://127.0.0.1:8000/';
      logging = true;
      console.log('Hello Kenny');
    } else if (location.hostname.split('.')[0] == 'www') {
      testingDomain = 'https://t.mobovidata.com/';
      logging = false;
    } else {
      testingDomain = 'https://staging.mobovidata.com/';
      logging = true;
    }

    function uuidExists() {
      var uid = _satellite.readCookie('mv_uid');
      return !(uid === undefined || uid === 'undefined');
    }

    function riidExists() {
      var cid = _satellite.readCookie('mv_cid');
      return !(cid == undefined || cid == 'undefined');
    }

    function sessionExists() {
      var sid = _satellite.readCookie('mv_sid');
      return !(sid == undefined || sid == 'undefined');
    }

    function strandsIdExists() {
      var stid = _satellite.readCookie('StrandsSBS_User');
      return !(stid == undefined || stid == 'undefined');
    }

    var dl = window.DATALAYER,
        pageType = dl.pageType;

    function setUUID(uuid) {
      _satellite.setCookie('mv_uid', uuid, 365*5);
      return _satellite.readCookie('mv_uid');
    }

    // Asks mobovidata for a UUID to use, sets cookie to that UUID and returns that UUID
    var mvd_ajax = {
      /*
        AJAX FUNCTIONS:
        requestUUID()
        verifyUUID()
        evalUser(riid)
        setRIID(email)

      AJAX WORKFLOWS:

      1. NEW USER (sessionExists() == False, uuidExists() == False)
        mvd_ajax.requestUUID().complete(function(data) {
          uuid = setUUID(data.responseJSON.uuid);
          makeTracker();
        });

      2. RETURNING USER (sessionExists() == False, uuidExists() == True)
        mvd_ajax.verifyUUID().complete(function(data) {
          uuid = setUUID(data.responseJSON.uuid);
          makeTracker();
        })

      3. EXISTING USER; EXISTING SESSION; EMAIL SUBMIT (sessionExists() == True, uuidExists() == True, EMAIL SUBMITTED)
        mvd_ajax.setRIID().complete(function(data) {
          var j = JSON.parse(data.responseText);
          _satellite.setCookie('mv_cid', j.result.recipientId, 365*5);
                mvd_ajax.evalUser(j.result.recipientId).complete(function(data) {
            if (data.responseJSON.eval_user_result == 'success') {
              setUUID(data.responseJSON.uuid);
            }
                });
        })

      4. EXISTING USER; NEW SESSION; NEW RIID; RIID IN TRACKING CODE (uuidExists() == True, sessionExists() == False, riidExists() == False, getURLParameter['dz_riid'] != undefined)
        Set RIID cookie, then evalUser function

      */

      requestUUID: function () {
        // console.log('----Executing: requestUUID()----');
        var sid = sessId,
            user_data = { sid: sid };
        if (riidExists()) {
          user_data['riid'] = _satellite.readCookie('mv_cid');
        }

        return jQuery.ajax({
          type: "POST",
          url: testingDomain + 'api/register_user',
          crossDomain: false,
          data: user_data,
          dataType: 'json'
        });
      },

      verifyUUID: function() {
        var uuid = getUUID(),
            user_data = { mvid: uuid };
        if (riidExists()) {
          user_data['riid'] = _satellite.readCookie('mv_cid');
        }

        return jQuery.ajax({
          type: "POST",
          url: testingDomain + 'api/check_uuid',
          crossDomain: false,
          data: user_data,
          dataType: 'json'
        });
      },

      // Checks if RIID already exists in mvd DB. If so, replaces existing mv_uid with matching uuid
      evalUser: function(riid) {
        var user_data = {riid: riid, mvid: getUUID()};
        // console.log('evaluating user data: ' + JSON.stringify(user_data));

        return jQuery.ajax({
          type: "POST",
          url: testingDomain + 'api/eval_user',
          crossDomain: false,
          data: user_data,
          dataType: 'json'
        });
      },

      //	Gets user RIID, saves as cookie, then transmits to server to check for existing UID
      setRIID: function(em) {
        var empty_ce = window.location.origin + '/responsys/api/fce?customEventName=empty_custom_event&customEventId=5805&rs-email='+em;
        return jQuery.ajax({
          type: 'POST',
          url: empty_ce
        });
      }
    };


    function mvdDispatcher() {
      /*  The only function called directly. Orchestrates data requests and compilations.
          2 basic steps:
              1. Create sessionID if not exists
              2. If UUID not exists, create
              3. If UUID exists, validate
              4. Use sessionID and UUID to make tracking param
      */
      // console.log('--mvdDispatcher');
      if (getUrlParameter['dz_riid']) {
        _satellite.setCookie('mv_cid', getUrlParameter['dz_riid'], 365*5);
      }
      if (!sessionExists()) {
        // This is the landing page, create a session ID
        // console.log('--mvdDispatcher_sessionExists()==False');
        sesh = createSession();

        if (!uuidExists()) {
          // This is the browser's first visit to the site
          mvd_ajax.requestUUID().complete(function(data) {
            // console.log('--requestUUID() Response:');
            // console.log(data);
            if (data.responseJSON && data.responseJSON.uuid) {
              uuid = setUUID(data.responseJSON.uuid);
              makeTracker(uuid, sesh);
            }
          });
        } else {
          // This browser has been to our site before
          // Verify that it's UUID is recognized by mobovidata
          // console.log('Checking UUID.....');
          mvd_ajax.verifyUUID().complete(function(data) {
            // console.log('UUID returned!');
            if (data.responseJSON && data.responseJSON.uuid) {
              uuid = setUUID(data.responseJSON.uuid);
              makeTracker(uuid, sesh);
            }
          });
        }
      } else {
        if (!uuidExists()) {
          // This is the browser's first visit to the site
          mvd_ajax.requestUUID().complete(function(data) {
            // console.log('--requestUUID() Response:');
            // console.log(data);
            if (data.responseJSON && data.responseJSON.uuid) {
              uuid = setUUID(data.responseJSON.uuid);
              makeTracker(uuid, sesh);
            }
          });
        }
        uuid = _satellite.readCookie('mv_uid');
        sesh = _satellite.readCookie('mv_sid');
        if (uuid == undefined || uuid == 'undefined' || sesh == undefined || sesh == 'undefined') {
          uuid = getCookie('mv_uid');
          sesh = getCookie('mv_sid');
        }

        makeTracker(uuid, sesh);
      }
    }

    function getCookie(cname) {
      var name = cname + "=",
          ca = document.cookie.split(';');
      for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1);
        if (c.indexOf(name) == 0) return c.substring(name.length,c.length);
      }
      return false;
    }

    function processEmail(em) {
      if (logging) console.log(em);
      try {
        mvd_ajax.setRIID(em).complete(function(data) {
          if (logging) console.log('---mvd_ajax.setRIID complete');

          var j = JSON.parse(data.responseText);
          _satellite.setCookie('mv_cid', j.result.recipientId, 365*5);

          mvd_ajax.evalUser(j.result.recipientId).complete(function(data) {
            if (logging) {
              console.log('evalUser complete');
              console.log(data);
            }
            if (data.responseJSON.eval_user_result == 'success') {
              setUUID(data.responseJSON.uuid);
              return {'riid': j.result.recipientId, 'uuid': data.responseJSON.uuid};
            }
          });
        });
      }
      catch (err) {}
    }

    // Gets uuid from cookie or gets UUID from MVD if cookie is missing
    function getUUID() {
      if (uuidExists()) {
        return _satellite.readCookie('mv_uid');
      } else {
        // console.log('----CALLER: getUUID()      CALLING: requestUUID----');
        mvd_ajax.requestUUID().complete(function(data) {
          // console.log('requestUUID complete');
          if (data.responseJSON && data.responseJSON.uuid) {
            return setUUID(data.responseJSON.uuid);
          }
        });
      }
    }

    function sessionID() {
      // Creates unique session IDs
      function s4() {
        return Math.floor((1 + Math.random()) * 0x10000)
          .toString(16)
          .substring(1);
      }
      return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
    }

    function createSession() {
      var sid = sessionID();
      _satellite.setCookie('mv_sid', sid);
      return sid;
    }

    function sessId() {
      return _satellite.readCookie('mv_sid');
    }

    function riid() {
      return riidExists() ? _satellite.readCookie('mv_cid') : '';
    }

    function strandsid() {
      return strandsIdExists() ? _satellite.readCookie('StrandsSBS_User') : '';
    }

    function getRequiredParams() {
      var reqParams = {
        mvid : '',
        mvsid : '',
        mvfv : 0,
        mvapi : '',
        strandsid : ''
      };
      if (strandsIdExists()) {
        reqParams['strandsid'] = strandsid();
      }
      if (riidExists()) {
        reqParams['mvrid'] = riid();
      } else if (window.DATALAYER.pageType == 'orderComplete') {
        // // Get RIID of this customer by registering email w/ Responsys
        // processEmail(window.DATALAYER.orderData.shipping.email);
        reqParams['mvrid'] = riid();
      }
      return reqParams;
    }

    function getCartData() {
      // return data and params relevant to cart pages
      return { mvcid: dl.cart.quoteId };
    }

    function getOrderData() {
      // return data and params relevant to order pages
      return { mvoid: dl.orderData.orderId };
    }

    function getProductPageData(pageParams) {
      /*
        Productview page params include:
        - mvbn: Brand Name
        - mvmn: Model Name
        - mvpid: ProductFullId
      */
      var bc = dl.pageData.breadCrumbs;
      if (dl && dl.pageData && bc ) {
        pageParams['mvbn'] = bc[0] != undefined ? bc[0].name : 'unknown brand';
        pageParams['mvmn'] = bc[1] != undefined ? bc[1].name : 'unknown model';
        pageParams['mvpid'] = dl.pageData.productFullId;
      }
      return pageParams;
    }

    function cleanPageParams() {
      /*
        Returns a newly concatenated version of the query parameters with the following replacements:
          = -> %eq%
          & -> %amp%
      */
      var substr = window.location.search.substring(1).split('&'),
          substr_new = [];
      for (var i = 0; i < ss.length; i++) { substr_new.push(substr[i].replace('=', '-%eq%-'));}
      substr = substr_new.join('-%amp%-');
      return substr;
    }

    function getPageviewData() {
      // @return: data and params relevant to pageviews that are not cart or order
      var pageParams = {
        mvt : pageType,
        mvsl : document.location.pathname,
        mvprm : window.location.search.substring(1),
        mvhdrs : encodeURIComponent(navigator.userAgent),
        mvcid : '',
        mvoid : '',
        mvst : '',
        mvdv : mvdDeviceDetector ? mvdDeviceDetector : 'no device found'
      };

      // TODO: Control for different page types
      if (pageType == 'product') {
        pageParams = getProductPageData(pageParams);
      } else if (pageType == 'category' || pageType == 'homepage') {
        pageParams['mvpt'] = pageType;
      }
      return pageParams;
    }

    function makePixel(params) {
      var i = new Image;
      i.src = testingDomain + 'api/tracking.gif?' + params;
      if (logging) console.log(i.src);
    }

    function makeString(object) {
      if (typeof object === 'object') {
        while (typeof object === 'object') {
          object = JSON.stringify(object);
        }
        return object;
      }
      return object;
    }

    function packageParams(paramsList) {
      // URL-encode parameters (if needed), and concat paramsList (list of dicts) to query string
      var urlParams = [];
      for (var i = 0; i < paramsList.length; i++) {
        var params = paramsList[i];
        for (key in params) {
          if (params[key] !== null && typeof params[key] === 'object') {
            params[key] = makeString(params[key]);
          }
          urlParams.push(key + '=' + params[key]);
        }
      }
      urlParams = urlParams.join('&');
      return urlParams;
    }

    /*
      Execution code starts here
        After logic flow we wind up with 2 objects that we have to json-ify and
        combine with & and =
    */
    function makeTracker(uuid, sessionId) {
      var requiredParams = getRequiredParams(),
          pageParams = getPageviewData();

      requiredParams.mvid = uuid;
      requiredParams.mvsid = sessionId;

      if (pageType == 'orderComplete') {
        // var pageParams = getOrderData();
        pageParams.mvoid = dl.orderData.orderId;
        processEmail(window.DATALAYER.orderData.shipping.email);
        requiredParams.mvrid = riid();
        requiredParams.mvapi = 'or';
      } else if (pageType == 'cart') {
        // var pageParams = getCartData();
        pageParams.mvcid = dl.cart.quoteId;
        requiredParams.mvapi = 'cr';
      } else {
        requiredParams.mvapi = 'pv';
      }
      var paramsList = [pageParams, requiredParams];

      makePixel(packageParams(paramsList));
    }

    // Email validator
    function validateEmail(email) {
      var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
      return re.test(email);
    }

    $(document).ready(function() {
      /*
        Set listeners on all possible email submit fields
      */
      $("#newsletter-validate-detail").submit(function () {
        // console.log('Email submit');
        var e = document.getElementById('newsletter').value;
        _satellite.setCookie('mv_ce', e);
        processEmail(e);
      });

      $("#discount-form-email").submit(function () {
        // console.log('Email submit');
        var e = document.getElementById('popup-discount-email').value;
        _satellite.setCookie('mv_ce', e);
        processEmail(e);
      });

      $("#discount-form-bottom").submit(function () {
        // console.log('Email submit');
        var e = document.getElementById('floating_emailfield').value;
        _satellite.setCookie('mv_ce', e);
        processEmail(e);
      });

      $("input[name='billing[email]']").change(function() {
        if (logging) {
          console.log('email changed');
        }
        var e = $(this).val();
        if (validateEmail(e)) {
          if (logging) console.log('validation passed');
          _satellite.setCookie('mv_ce', e);
          processEmail(e);
        }
      });

      try { mvdDispatcher() }
      catch(err) { console.log(err) }
    });
  }
})(jQuery);
