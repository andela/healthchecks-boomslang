from hc.api.models import Channel
from hc.test import BaseTestCase


class VerifyEmailTestCase(BaseTestCase):

    def setUp(self):
        super(VerifyEmailTestCase, self).setUp()
        self.channel = Channel(user=self.alice, kind="email")
        self.channel.value = "alice@example.org"
        self.channel.save()

    def test_it_works(self):
        token = self.channel.make_token()
        url = "/integrations/%s/verify/%s/" % (self.channel.code, token)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        channel = Channel.objects.get(code=self.channel.code)
        self.assertTrue(channel.email_verified)

    def test_missing_channel(self):
        # Valid UUID, and even valid token but there is no channel for it:
        code = "6837d6ec-fc08-4da5-a67f-08a9ed1ccf62"
        token = self.channel.make_token()
        url = "/integrations/%s/verify/%s/" % (code, token)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_it_handles_bad_token(self):
        """This test handles bad token"""
        token = "just a guessed token"
        url = "/integrations/%s/verify/%s/" % (self.channel.code, token)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
