from django.contrib.auth.hashers import make_password
from hc.test import BaseTestCase


class CheckTokenTestCase(BaseTestCase):

    def setUp(self):
        super(CheckTokenTestCase, self).setUp()
        self.profile.token = make_password("secret-token")
        self.profile.save()

    def test_it_shows_form(self):
        r = self.client.get("/accounts/check_token/alice/secret-token/")
        self.assertContains(r, "You are about to log in")

    def test_it_redirects(self):
        response = self.client.post("/accounts/check_token/alice/secret-token/")
        self.assertRedirects(response, "/checks/")

        # After login, token should be blank
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.token, "")

    ### Login and test it redirects already logged in
        self.assertEqual(response.status_code, 302)

    ### Login with a bad token and check that it redirects
        c = self.client.post("/accounts/check_token/rose/secret-token/")
        self.assertEqual(c.status_code, 302)