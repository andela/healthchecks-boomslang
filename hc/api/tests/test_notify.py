import json

from django.core import mail
from django.test import override_settings
from hc.api.models import Channel, Check, Notification
from hc.test import BaseTestCase
from mock import patch
from requests.exceptions import ConnectionError, Timeout


class NotifyTestCase(BaseTestCase):

    def _setup_data(self, kind, value, status="down", email_verified=True):
        self.check = Check()
        self.check.status = status
        self.check.user = self.alice
        self.check.save()

        self.channel = Channel(user=self.alice)
        self.channel.kind = kind
        self.channel.value = value
        self.channel.email_verified = email_verified
        self.channel.save()
        self.channel.checks.add(self.check)

    @patch("hc.api.transports.requests.request")
    def test_webhook(self, mock_get):
        self._setup_data("webhook", "http://example")
        mock_get.return_value.status_code = 200

        self.channel.notify(self.check)
        mock_get.assert_called_with(
            "get", u"http://example",
            headers={"User-Agent": "healthchecks.io"}, timeout=5)

    @patch("hc.api.transports.requests.request", side_effect=Timeout)
    def test_webhooks_handle_timeouts(self, mock_get):
        self._setup_data("webhook", "http://example")
        self.channel.notify(self.check)

        n = Notification.objects.get()
        self.assertEqual(n.error, "Connection timed out")

    @patch("hc.api.transports.requests.request", side_effect=ConnectionError)
    def test_webhooks_handle_connection_errors(self, mock_get):
        self._setup_data("webhook", "http://example")
        self.channel.notify(self.check)

        n = Notification.objects.get()
        # Test that the web hooks handle connection errors
        self.assertEqual(n.error, "Connection failed")

    @patch("hc.api.transports.requests.request")
    def test_webhooks_handle_error_500(self, mock_get):

        self._setup_data("webhook", "http://example")
        self.channel.notify(self.check)
        # Test that the web hooks handle error 500s
        mock_get.return_value.status_code = 500

    @patch("hc.api.transports.requests.request")
    def test_webhooks_ignore_up_events(self, mock_get):
        self._setup_data("webhook", "http://example", status="up")
        self.channel.notify(self.check)

        self.assertFalse(mock_get.called)
        self.assertEqual(Notification.objects.count(), 0)

    @patch("hc.api.transports.requests.request")
    def test_webhooks_support_variables(self, mock_get):
        template = "http://host/$CODE/$STATUS/$TAG1/$TAG2/?name=$NAME"
        self._setup_data("webhook", template)
        self.check.name = "Hello World"
        self.check.tags = "foo bar"
        self.check.save()

        self.channel.notify(self.check)

        url = u"http://host/%s/down/foo/bar/?name=Hello%%20World" \
            % self.check.code

        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "get")
        self.assertEqual(args[1], url)
        self.assertEqual(kwargs["headers"], {"User-Agent": "healthchecks.io"})
        self.assertEqual(kwargs["timeout"], 5)

    @patch("hc.api.transports.requests.request")
    def test_webhooks_support_post(self, mock_request):
        template = "http://example.com\n\nThe Time Is $NOW"
        self._setup_data("webhook", template)
        self.check.save()

        self.channel.notify(self.check)
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "post")
        self.assertEqual(args[1], "http://example.com")

        # spaces should not have been urlencoded:
        self.assertTrue(kwargs["data"].startswith("The Time Is 2"))

    @patch("hc.api.transports.requests.request")
    def test_webhooks_dollarsign_escaping(self, mock_get):
        # If name or tag contains what looks like a variable reference,
        # that should be left alone:

        template = "http://host/$NAME"
        self._setup_data("webhook", template)
        self.check.name = "$TAG1"
        self.check.tags = "foo"
        self.check.save()

        self.channel.notify(self.check)

        url = u"http://host/%24TAG1"
        mock_get.assert_called_with(
            "get", url, headers={"User-Agent": "healthchecks.io"}, timeout=5)

    @patch("hc.api.transports.requests.request")
    def test_webhook_fires_on_up_event(self, mock_get):
        self._setup_data("webhook", "http://foo\nhttp://bar", status="up")

        self.channel.notify(self.check)

        mock_get.assert_called_with(
            "get", "http://bar", headers={"User-Agent": "healthchecks.io"},
            timeout=5)

    def test_email(self):
        self._setup_data("email", "alice@example.org")
        self.channel.notify(self.check)

        n = Notification.objects.get()
        self.assertEqual(n.error, "")

        # And email should have been sent
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertTrue("X-Bounce-Url" in email.extra_headers)

    def test_it_skips_unverified_email(self):
        self._setup_data("email", "alice@example.org", email_verified=False)
        self.channel.notify(self.check)

        assert Notification.objects.count() == 1
        n = Notification.objects.first()
        self.assertEqual(n.error, "Email not verified")
        self.assertEqual(len(mail.outbox), 0)

    @patch("hc.api.transports.requests.request")
    def test_pd(self, mock_post):
        self._setup_data("pd", "123")
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        self.assertEqual(payload["event_type"], "trigger")

    @patch("hc.api.transports.requests.request")
    def test_slack(self, mock_post):
        self._setup_data("slack", "123")
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        attachment = payload["attachments"][0]
        fields = {f["title"]: f["value"] for f in attachment["fields"]}
        self.assertEqual(fields["Last Ping"], "Never")

    @patch("hc.api.transports.requests.request")
    def test_slack_with_complex_value(self, mock_post):
        v = json.dumps({"incoming_webhook": {"url": "123"}})
        self._setup_data("slack", v)
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        args, kwargs = mock_post.call_args
        self.assertEqual(args[1], "123")

    @patch("hc.api.transports.requests.request")
    def test_slack_handles_500(self, mock_post):
        self._setup_data("slack", "123")
        mock_post.return_value.status_code = 500

        self.channel.notify(self.check)

        n = Notification.objects.get()
        self.assertEqual(n.error, "Received status code 500")

    @patch("hc.api.transports.requests.request", side_effect=Timeout)
    def test_slack_handles_timeout(self, mock_post):
        self._setup_data("slack", "123")

        self.channel.notify(self.check)

        n = Notification.objects.get()
        self.assertEqual(n.error, "Connection timed out")

    @patch("hc.api.transports.requests.request")
    def test_hipchat(self, mock_post):
        self._setup_data("hipchat", "123")
        mock_post.return_value.status_code = 204

        self.channel.notify(self.check)
        n = Notification.objects.first()
        self.assertEqual(n.error, "")

        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        self.assertIn("DOWN", payload["message"])

    @patch("hc.api.transports.requests.request")
    def test_opsgenie(self, mock_post):
        self._setup_data("opsgenie", "123")
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)
        n = Notification.objects.first()
        self.assertEqual(n.error, "")

        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        self.assertIn("DOWN", payload["message"])

    @patch("hc.api.transports.requests.request")
    def test_pushover(self, mock_post):
        self._setup_data("po", "123|0")
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        args, kwargs = mock_post.call_args
        payload = kwargs["data"]
        self.assertIn("DOWN", payload["title"])

    @patch("hc.api.transports.requests.request")
    def test_victorops(self, mock_post):
        self._setup_data("victorops", "123")
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        self.assertEqual(payload["message_type"], "CRITICAL")

    @patch("hc.api.transports.requests.request")
    def test_discord(self, mock_post):
        v = json.dumps({"webhook": {"url": "123"}})
        self._setup_data("discord", v)
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        attachment = payload["attachments"][0]
        fields = {f["title"]: f["value"] for f in attachment["fields"]}
        self.assertEqual(fields["Last Ping"], "Never")

    @patch("hc.api.transports.requests.request")
    def test_pushbullet(self, mock_post):
        self._setup_data("pushbullet", "fake-token")
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["type"], "note")
        self.assertEqual(kwargs["headers"]["Access-Token"], "fake-token")
