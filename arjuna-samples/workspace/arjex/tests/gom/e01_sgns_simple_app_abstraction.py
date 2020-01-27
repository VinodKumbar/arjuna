import unittest
import time

from arjuna.tpi import Arjuna
from arjuna.interact.gui.helpers import With
from arjuna.interact.gui.gom import WebApp

class WPBaseTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Arjuna.init("/Users/rahulverma/Documents/github_tm/arjuna/arjuna-samples/workspace/arjex")
        self.__config = Arjuna.get_ref_config()
        self.__app = None

    @property
    def wordpress(self):
        return self.__app

    @property
    def config(self):
        return self.__config

    def setUp(self):
        self.__app = WebApp(base_url=self.config.get_user_option_value("wp.login.url").as_str())
        self.wordpress.launch()
        self.wordpress.ui.externalize_guidef(ns_dir="sgns_wordpress_singlefile", def_file_name="WordPress.gns")
        self.login_with_default_creds()

    def tearDown(self):
        self.logout()
        #self.app.automator.quit()

    def login_with_default_creds(self):
        user, pwd = self.config.get_user_option_value("wp.users.admin").split_as_str_list()

        # Login
        self.wordpress.ui.element(With.gns_name("login").format(RoLe="user")).text = user
        self.wordpress.ui.element(With.gns_name("password").format(roLE="user")).text = pwd
        self.wordpress.ui.element("submit").click()

        self.wordpress.ui.element("view_site").wait_until_visible()

    def logout(self):
        url = self.config.get_user_option_value("wp.logout.url").as_str()
        self.wordpress.ui.browser.go_to_url(url)

        self.wordpress.ui.element("logout_confirm").click()
        self.wordpress.ui.element("logout_msg").wait_until_visible()

class SimpleAppTest(WPBaseTest):

    def test_author_type_selection(self):
        self.wordpress.ui.element("Settings").click()

        role_select = self.wordpress.ui.dropdown("role")
        role_select.select_value("editor")

        self.assertEqual("editor", role_select.value, "Author type selection failed.")

unittest.main()