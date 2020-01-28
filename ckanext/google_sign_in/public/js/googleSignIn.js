var currentGoogleUser = {}
var auth2;
var cid = getMetaContent('google-signin-client_id');
var hd = getMetaContent('google-signin-hosted_domain');

var startApp = function () {
  gapi.load('auth2', function() {
      auth2 = gapi.auth2.init({
        client_id: cid
      });

      attachSignin(document.getElementById('google-button-login'));
  });
};

function attachSignin(element) {
  auth2.attachClickHandler(element, {},
    function(googleUser) {
      var profile = googleUser.getBasicProfile();
      var response = googleUser.getAuthResponse();

      $.post("/postmethod", {
          'name': profile.getName(), 
          'email': profile.getEmail(),
          'id_token': response['id_token'], 
          'token': response['access_token'],
          'came_from': '/user/logged_in'
      },
      function(response){
        window.location.href = "/dashboard"
      })
      
    }, function(error) {
        console.log("Erro = " + error)
      }
  );
}

function getMetaContent(propName) {
  var metas = document.getElementsByTagName('meta');
  for (i = 0; i < metas.length; i++) {
    if (metas[i].getAttribute("name") == propName) {
      return metas[i].getAttribute("content");
    }
  }
  return "";
}

function onSignIn(googleUser) {
  currentGoogleUser = googleUser;
  var profile = googleUser.getBasicProfile();
  var id_token = googleUser.getAuthResponse().id_token;
}