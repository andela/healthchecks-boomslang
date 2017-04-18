from hc.test import BaseTestCase
from hc.api.models import Check


class SwitchTeamTestCase(BaseTestCase):

    def test_it_switches(self):
        c = Check(user=self.alice, name="This belongs to Alice")
        c.save()

        self.client.login(username="bob@example.org", password="password")

        url = "/accounts/switch_team/%s/" % self.alice.username
        r = self.client.get(url, follow=True)

        ### Assert the contents of r

    def test_it_checks_team_membership(self):
        self.client.login(username="charlie@example.org", password="password")

        url = "/accounts/switch_team/%s/" % self.alice.username
        r = self.client.get(url)
        ### Assert the expected error code

    def test_it_switches_to_own_team(self):
        self.client.login(username="alice@example.org", password="password")

        url = "/accounts/switch_team/%s/" % self.alice.username
        r = self.client.get(url, follow=True)

        ### Assert the expected response code

    def test_it_handles_invalid_username(self):
        self.client.login(username="bob@example.org", password="password")

        url = "/accounts/switch_team/dave/"
        r = self.client.get(url)
        self.assertEqual(r.status_code, 403)

    def test_it_requires_login(self):
        url = "/accounts/switch_team/%s/" % self.alice.username
        r = self.client.get(url)

        expected_url = "/accounts/login/?next=/accounts/switch_team/alice/"
        self.assertRedirects(r, expected_url)
