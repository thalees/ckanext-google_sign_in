# encoding: utf-8

from ckan.lib.base import BaseController, request
from ckan.controllers.user import UserController
import ckan.logic as logic
import requests
import os

site = os.environ.get('CKAN_SITE_URL', '')
get_action = logic.get_action

class ValidationGoogleUserController(UserController):
    def post_data(self):
        ENDPOINT = '/user/logged_in'
        
        self.login(self)

        requests.post(url = site + ENDPOINT, data = {})
