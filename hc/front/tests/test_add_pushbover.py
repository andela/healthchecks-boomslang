from django.test.utils import override_settings
from hc.api.models import Channel
from hc.test import BaseTestCase


@override_settings(PUSHOVER_API_TOKEN="token", PUSHOVER_SUBSCRIPTION_URL="url")
class AddPushoverTestCase(BaseTestCase):
    def test_instructions_work(self):
        self.client.login(username="alice@example.org", password="password")
        resp = self.client.get("/integrations/add_pushover/")
        self.assertContains(resp, "Subscribe with Pushover")

    def test_it_adds_channel(self):
        self.client.login(username="alice@example.org", password="password")

        session = self.client.session
        session["po_nonce"] = "n"
        session.save()

        params = "pushover_user_key=a&nonce=n&prio=0"
        resp = self.client.get("/integrations/add_pushover/?%s" % params)
        self.assertEqual(resp.status_code, 302)

        channels = list(Channel.objects.all())
        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0].value, "a|0")

    @override_settings(PUSHOVER_API_TOKEN=None)
    def test_it_requires_api_token(self):
        self.client.login(username="alice@example.org", password="password")
        resp = self.client.get("/integrations/add_pushover/")
        self.assertEqual(resp.status_code, 404)

    # Test that pushover validates priority
    def test_push_over_validates_priority(self):
        self.client.login(username="alice@example.org", password="password")
        session = self.client.session
        session["po_nonce"] = "n"
        session.save()

        params = "pushover_user_key=a&nonce=n&prio=8"
        resp = self.client.get("/integrations/add_pushover/?%s" % params)
        self.assertEqual(resp.status_code, 400)

    def test_it_validates_nonce(self):
        self.client.login(username="alice@example.org", password="password")

        session = self.client.session
        session["po_nonce"] = "n"
        session.save()

        params = "pushover_user_key=a&nonce=INVALID&prio=0"
        resp = self.client.get("/integrations/add_pushover/?%s" % params)
        self.assertEqual(resp.status_code, 403)
