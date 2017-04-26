from hc.api.models import Check
from hc.test import BaseTestCase


class AddCheckTestCase(BaseTestCase):

    def test_it_works(self):
        url = "/checks/add/"
        self.client.login(username="alice@example.org", password="password")
        resp = self.client.post(url)
        self.assertRedirects(resp, "/checks/")
        assert Check.objects.count() == 1

    # ##Test that team access works
    def test_team_access_works(self):
        url = "/checks/add/"
        self.client.login(username="bob@example.org", password="password")
        # import ipdb; ipdb.set_trace()
        resp = self.client.post(url)
        self.assertRedirects(resp, "/checks/")
        assert Check.objects.count() == 1

    def test_it_rejects_get(self):
        url = "/checks/add/"
        self.client.login(username="alice@example.org", password="password")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)
