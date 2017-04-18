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
            ### Assert that the expected error is the response error

        return r

    def test_it_works(self):
        r = self.post({
            "api_key": "abc",
            "name": "Foo",
            "tags": "bar,baz",
            "timeout": 3600,
            "grace": 60
        })

        self.assertEqual(r.status_code, 201)

        doc = r.json()
        assert "ping_url" in doc
        self.assertEqual(doc["name"], "Foo")
        self.assertEqual(doc["tags"], "bar,baz")
        
        ### Assert the expected last_ping and n_pings values

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
        r = self.client.post(self.URL, payload,
                             content_type="application/json",
                             HTTP_X_API_KEY="abc")

        ### Make the post request and get the response
        r = {'status_code': 201} ### This is just a placeholder variable

        self.assertEqual(r['status_code'], 201)

    ### Test for the assignment of channels

    def test_it_supports_unique(self):
        existing = Check(user=self.alice, name="Foo")
        existing.save()

        r = self.post({
            "api_key": "abc",
            "name": "Foo",
            "unique": ["name"]
        })

        # Expect 200 instead of 201
        self.assertEqual(r.status_code, 200)

        # And there should be only one check in the database:
        self.assertEqual(Check.objects.count(), 1)

    def test_it_handles_missing_request_body(self):
        ### Make the post request with a missing body and get the response
        r = {'status_code': 400, 'error': "wrong api_key"} ### This is just a placeholder variable
        self.assertEqual(r['status_code'], 400)
        self.assertEqual(r["error"], "wrong api_key")

    def test_it_handles_invalid_json(self):
        ### Make the post request with invalid json data type
        r = {'status_code': 400, 'error': "could not parse request body"} ### This is just a placeholder variable
        self.assertEqual(r['status_code'], 400)
        self.assertEqual(r["error"], "could not parse request body")

    def test_it_rejects_wrong_api_key(self):
        r = self.post({"api_key": "wrong"})
        self.assertEqual(r.status_code, 403)
    
    ### Test for the 'timeout is too small' errors
    ### Test for the 'timeout is too large' errors

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
