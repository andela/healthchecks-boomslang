from django.core import mail

from hc.test import BaseTestCase
from hc.accounts.models import Member
from hc.api.models import Check
from django.conf import settings


class ProfileTestCase(BaseTestCase):

    def test_it_sends_set_password_link(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"set_password": "1"}
        response = self.client.post("/accounts/profile/", form)
        assert response.status_code == 302

        # profile.token should be set now
        self.alice.profile.refresh_from_db()

        token = self.alice.profile.token

        self.assertTrue(len(token) > 10)

        # Assert that the token is set
        self.assertEqual(response.status_code, 302)

        # Assert that the email was sent and check email content
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Here's a link to set a password for your account on {}:".format(settings.SITE_NAME), mail.outbox[0].body)

    def test_it_creates_api_key(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"create_api_key": "1"}
        response = self.client.post("/accounts/profile/", form)

        # Test it creates API key
        self.assertContains(response, 'The API key has been created!')

    def test_it_revokes_api_key(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"revoke_api_key": "1"}

        response = self.client.post("/accounts/profile/", form)
        # Test it revokes API key
        self.assertContains(response, "The API key has been revoked!")

    def test_it_sends_report(self):
        check = Check(name="Test Check", user=self.alice)
        check.save()

        self.alice.profile.send_report()

        # Assert that the email was sent and check email content
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("This is a monthly report sent by {}.".format(settings.SITE_NAME), mail.outbox[0].body)

    def test_it_adds_team_member(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"invite_team_member": "1", "email": "frank@example.org"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 200

        member_emails = set()
        for member in self.alice.profile.member_set.all():
            member_emails.add(member.user.email)

        # Assert the existence of the member emails
        self.assertTrue("frank@example.org" in member_emails)

        # Assert that the email was sent and check email content
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("You will be able to manage their existing monitoring checks and set up new\nones.", mail.outbox[0].body)

    def test_add_team_member_checks_team_access_allowed_flag(self):
        self.client.login(username="charlie@example.org", password="password")

        form = {"invite_team_member": "1", "email": "frank@example.org"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 403

    def test_it_removes_team_member(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"remove_team_member": "1", "email": "bob@example.org"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 200

        self.assertEqual(Member.objects.count(), 0)

        self.bobs_profile.refresh_from_db()
        self.assertEqual(self.bobs_profile.current_team, None)

    def test_it_sets_team_name(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"set_team_name": "1", "team_name": "Alpha Team"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 200

        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.team_name, "Alpha Team")

    def test_set_team_name_checks_team_access_allowed_flag(self):
        self.client.login(username="charlie@example.org", password="password")

        form = {"set_team_name": "1", "team_name": "Charlies Team"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 403

    def test_it_switches_to_own_team(self):
        self.client.login(username="bob@example.org", password="password")

        self.client.get("/accounts/profile/")

        # After visiting the profile page, team should be switched back
        # to user's default team.
        self.bobs_profile.refresh_from_db()
        self.assertEqual(self.bobs_profile.current_team, self.bobs_profile)
