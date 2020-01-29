import os
from json import dumps
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
from beaker.session import Session as BeakerSession
from ckan.common import _, ungettext, c, request, session, json
from ckan.model import User
from ckan.controllers.user import UserController
import json
import uuid
import pylons.config as config
import ckan.lib.helpers as helpers
import requests
import re

# get 'GOOGLE__AUTH__KEY' from .env file
def get_client_id():
    return os.environ.get('GOOGLE__AUTH__KEY', '')


# get 'GOOGLE__HOSTED__DOMAIN' from .env file
def get_hosted_domain():
    return os.environ.get('GOOGLE__HOSTED__DOMAIN', '')


def omit_domain():
    return toolkit.asbool(
        config.get('ckan.googleauth_omit_domain_from_username',
                   False))


def email_to_ckan_user(email):
    if omit_domain():
        email = email.rsplit('@', 2)[0]

    return re.sub('[^A-Za-z0-9]+', '_', email)


class GoogleAuthException(Exception):
    pass

class Google_Sign_InPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthenticator)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes)


    def before_map(self, map):
        map.connect(
            '/postmethod',
            controller='ckanext.google_sign_in.controllers.validator:ValidationGoogleUserController',
            action= u'post_data'
        )
        return map
    
    def after_map(self, map):
        return map

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'google_sign_in')

    # declare new helper functions
    def get_helpers(self):
        return {
            'googleauth_get_client_id': get_client_id,
		    'googleauth_get_hosted_domain': get_hosted_domain
        }

    # verify email address within token
    def verify_email(self, token):
        res = requests.post('https://www.googleapis.com/oauth2/v3/tokeninfo?id_token=' + token, verify=True)
        
        if res.ok:
            is_email_verified = json.loads(res.content)
            if is_email_verified['email_verified'] == 'true':
                email_verified = is_email_verified['email']
                return email_verified
            else:
                raise GoogleAuthException(is_email_verified)
        else:
            raise GoogleAuthException(res)

    #if exist returns ckan user
    def get_ckanuser(self, user):
        user_ckan = User.by_name(user)

        if user_ckan:
            user_dict = toolkit.get_action('user_show')(data_dict={'id': user_ckan.id})
            return user_dict
        else:
            return None

    #generates a strong password
    def get_ckanpasswd(self):
        import datetime
        import random

        passwd = str(random.random())+ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")+str(uuid.uuid4().hex)
        passwd = re.sub(r"\s+", "", passwd, flags=re.UNICODE)
        return passwd


    def _logout_user(self):
	    # to revoke the Google token uncomment the code below

        # if 'ckanext-google-accesstoken' in session:
        #     atoken = session.get('ckanext-google-accesstoken')
        #     res = requests.get('https://accounts.google.com/o/oauth2/revoke?token=' + atoken)
        #     if res.status_code == 200:
        #    	    del session['ckanext-google-accesstoken']
        #     else:
        # 	    raise GoogleAuthException('Token not revoked')

        if 'ckanext-google-user' in session:
            del session['ckanext-google-user']
        if 'ckanext-google-email' in session:
            del session['ckanext-google-email']
        session.save()

    # at every access the email address is checked. if it is authorized ckan username is created and access is given
    def login(self):
    	params = toolkit.request.params

        if 'id_token' in params:
            try:
                mail_verified = self.verify_email(params["id_token"])
            except GoogleAuthException, e:
                toolkit.abort(500)

            user_account = email_to_ckan_user(mail_verified)

            user_ckan = self.get_ckanuser(user_account)

            if not user_ckan:
                user_ckan = toolkit.get_action('user_create')(
                                        context={'ignore_auth': True},
                                        data_dict={'email': mail_verified,
                                            'name': user_account,
                                            'password': self.get_ckanpasswd()})


            session['ckanext-google-user'] = user_ckan['name']
            session['ckanext-google-email'] = mail_verified

            #to revoke the Google token uncomment the code below
            session['ckanext-google-accesstoken'] = params['token']

            session.modified = True

            session.save()

            self.identify()

    # if someone is logged in will be set the parameter c.user
    def identify(self):
        user_ckan = session.get('ckanext-google-user')
        if user_ckan:
            c.user = user_ckan
        

    def logout(self):
        self._logout_user()

    def abort(self, status_code=None, detail='', headers=None, comment=None):
        self._logout_user()

        return (status_code, detail, headers, comment)
