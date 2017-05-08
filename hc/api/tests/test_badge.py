from django.conf import settings
from django.core.signing import base64_hmac

from hc.api.models import Check
from hc.test import BaseTestCase


class BadgeTestCase(BaseTestCase):

    def setUp(self):
        super(BadgeTestCase, self).setUp()
        self.check = Check.objects.create(user=self.alice, tags="foo bar")

    def test_it_rejects_bad_signature(self):
        resp = self.client.get("/badge/{}/12345678/foo.svg" .format(self.alice.username))

        self.assertEqual(resp.status_code, 404)

    def test_it_returns_svg(self):
        sig = base64_hmac(str(self.alice.username), "foo", settings.SECRET_KEY)
        sig = sig[:8].decode("utf-8")
        url = "/badge/{}/{}/foo.svg".format(self.alice.username, sig)
        resp = self.client.get(url)

        self.assertContains(resp, "svg", status_code=200)
