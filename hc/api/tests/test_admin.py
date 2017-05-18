from hc.api.models import Channel, Check
from hc.test import BaseTestCase


class ApiAdminTestCase(BaseTestCase):

    def setUp(self):
        super(ApiAdminTestCase, self).setUp()
        self.check = Check.objects.create(user=self.alice, tags="foo bar")

        ### Set Alice to be staff and superuser and save her :)

    def test_it_shows_channel_list_with_pushbullet(self):
        self.client.login(username="alice@example.org", password="password")

        Channel.objects.create(user=self.alice, kind="pushbullet",
                               value="test-token")

        ### Assert for the push bullet

    def test_it_shows_channel_list_with_unverified_email(self):
        self.client.login(username="alice@example.org", password="password")
        Channel.objects.create(user=self.alice, kind="email",
                               value="foo@example.org")

        r = self.client.get("/admin/api/channel/")
        self.assertEqual(r.status_code, 302)
        
