import json

from hc.api.models import Channel, Check
from hc.test import BaseTestCase


class CreateCheckTestCase(BaseTestCase):
    URL = "/api/v1/checks/"

    def post(self, data, expected_error=None, expected_fragment=None):
        r = self.client.post(self.URL, json.dumps(data),
                             content_type="application/json")

        if expected_error:
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.json()["error"], expected_error)

        if expected_fragment:

            self.assertEqual(r.status_code, 400)
            self.assertIn(expected_fragment, r.json()['error'])
            # Assert that the expected error is the response error

        return r

    def test_it_works(self):
        resp = self.post({
            "api_key": "abc",
            "name": "Foo",
            "tags": "bar,baz",
            "timeout": 3600,
            "grace": 60
        })

        self.assertEqual(resp.status_code, 201)

        doc = resp.json()
        assert "ping_url" in doc
        self.assertEqual(doc["name"], "Foo")
        self.assertEqual(doc["tags"], "bar,baz")
        self.assertEqual(doc["last_ping"], None)
        self.assertEqual(doc["n_pings"], 0)

        self.assertTrue("schedule" not in doc)
        self.assertTrue("tz" not in doc)

        self.assertEqual(Check.objects.count(), 1)
        check = Check.objects.get()
        self.assertEqual(check.name, "Foo")
        self.assertEqual(check.tags, "bar,baz")
        self.assertEqual(check.timeout.total_seconds(), 3600)
        self.assertEqual(check.grace.total_seconds(), 60)

    def test_it_accepts_api_key_in_header(self):
        payload = json.dumps({"name": "Foo"})
        resp = self.client.post(self.URL, payload,
                                content_type="application/json",
                                HTTP_X_API_KEY="abc")

        self.assertEqual(resp.status_code, 201)

    def test_channel_assignment(self):

        check = Check()
        check.status = "up"
        check.user = self.alice
        check.save()

        channel = Channel(user=self.alice)
        channel.save()
        channel.checks.add(check)
        count_before = channel.checks.count()
        resp = self.post({
            "api_key": "abc",
            "channels": "*"
        })
        count_after = channel.checks.count()
        self.assertEqual((count_after - count_before), 1)

    def test_it_supports_unique(self):
        existing = Check(user=self.alice, name="Foo")
        existing.save()

        r = self.post({
            "api_key": "abc",
            "name": "Foo",
            "unique": ["name"]
        })

        self.assertEqual(r.status_code, 200)

        self.assertEqual(Check.objects.count(), 1)

    def test_it_handles_missing_request_body(self):

        resp = self.post({})
        self.assertEqual(resp.status_code, 400)

    def test_it_handles_invalid_json(self):
        form = {"email": "alice@example.org"}
        resp = self.post(form)
        self.assertEqual(resp.status_code, 400)

    def test_it_rejects_wrong_api_key(self):
        r = self.post({"api_key": "wrong"})
        self.assertEqual(r.status_code, 403)

    def test_timeout_is_too_small(self):
        self.post({"api_key": "abc", "timeout": 1},
                  expected_fragment="timeout is too small")

    def test_timeout_is_too_large(self):
        resp = self.post({"api_key": "abc", "timeout": 36000000},
                         expected_fragment="timeout is too large")

    def test_it_rejects_non_number_timeout(self):
        self.post({"api_key": "abc", "timeout": "oops"},
                  expected_fragment="timeout is not a number")

    def test_it_rejects_non_string_name(self):
        self.post({"api_key": "abc", "name": False},
                  expected_fragment="name is not a string")

    def test_it_rejects_long_name(self):
        self.post({"api_key": "abc", "name": "01234567890" * 20},
                  expected_fragment="name is too long")

    def test_unique_accepts_only_whitelisted_values(self):
        existing = Check(user=self.alice, name="Foo")
        existing.save()

        self.post({
            "api_key": "abc",
            "name": "Foo",
            "unique": ["status"]
        }, expected_fragment="unexpected value")

    def test_it_rejects_bad_unique_values(self):
        self.post({
            "api_key": "abc",
            "name": "Foo",
            "unique": "not a list"
        }, expected_fragment="not an array")

    def test_it_supports_cron_syntax(self):
        r = self.post({
            "api_key": "abc",
            "schedule": "5 * * * *",
            "tz": "Europe/Riga",
            "grace": 60
        })

        self.assertEqual(r.status_code, 201)

        doc = r.json()
        self.assertEqual(doc["schedule"], "5 * * * *")
        self.assertEqual(doc["tz"], "Europe/Riga")
        self.assertEqual(doc["grace"], 60)

        self.assertTrue("timeout" not in doc)

    def test_it_validates_cron_expression(self):
        r = self.post({
            "api_key": "abc",
            "schedule": "not-a-cron-expression",
            "tz": "Europe/Riga",
            "grace": 60
        })

        self.assertEqual(r.status_code, 400)

    def test_it_validates_timezone(self):
        r = self.post({
            "api_key": "abc",
            "schedule": "* * * * *",
            "tz": "not-a-timezone",
            "grace": 60
        })

        self.assertEqual(r.status_code, 400)

    def test_it_sets_default_timeout(self):
        r = self.post({"api_key": "abc"})

        self.assertEqual(r.status_code, 201)

        doc = r.json()
        self.assertEqual(doc["timeout"], 86400)
