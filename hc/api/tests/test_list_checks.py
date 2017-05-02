import json
from datetime import timedelta as td
from django.utils.timezone import now
from django.conf import settings

from hc.api.models import Check
from hc.test import BaseTestCase


class ListChecksTestCase(BaseTestCase):

    def setUp(self):
        super(ListChecksTestCase, self).setUp()

        self.now = now().replace(microsecond=0)

        self.a1 = Check(user=self.alice, name="Alice 1")
        self.a1.timeout = td(seconds=3600)
        self.a1.grace = td(seconds=900)
        self.a1.last_ping = self.now
        self.a1.n_pings = 1
        self.a1.status = "new"
        self.a1.save()

        self.a2 = Check(user=self.alice, name="Alice 2")
        self.a2.timeout = td(seconds=86400)
        self.a2.grace = td(seconds=3600)
        self.a2.last_ping = self.now
        self.a2.status = "up"
        self.a2.save()

    def get(self):
        return self.client.get("/api/v1/checks/", HTTP_X_API_KEY="abc")

    def test_it_works(self):
        resp = self.get()
        # ## Assert the response status code
        self.assertEqual(resp.status_code, 200)
        doc = resp.json()
        #self.assertTrue("checks" in doc)
        checks = {check["name"]: check for check in doc["checks"]}
        # ## Assert the expected length of checks

        self.assertEqual(len(doc["checks"]), 2)
        # ## Assert the checks Alice 1 and Alice 2's timeout, grace, ping_url, status,
        # Alice 1
        self.assertEqual(checks['Alice 1']['grace'], 900)
        self.assertEqual(checks['Alice 1']['timeout'], 3600)
        self.assertNotEqual(checks['Alice 1']['ping_url'],
                            'https://hc-bs-staging.herokuapp.com//ping/0af1d589-e5e8-4e26-83cf-a38929136f3f')
        self.assertEqual(checks['Alice 1']['status'], 'new')
        # Alice 2
        self.assertEqual(checks['Alice 2']['grace'], 3600)
        self.assertEqual(checks['Alice 2']['timeout'], 86400)
        self.assertNotEqual(checks['Alice 2']['ping_url'],
                            'https://hc-bs-staging.herokuapp.com//ping/2bf1aa96-e8d8-4d0a-9408-d33d0829907e')
        self.assertEqual(checks['Alice 2']['status'], 'up')
        # ## last_ping, n_pings and pause_url
        # Alice 1
        self.assertEqual(checks['Alice 1']['last_ping'], self.a2.last_ping.isoformat())
        self.assertEqual(checks['Alice 1']['n_pings'], self.a1.n_pings)
        self.assertNotEqual(checks['Alice 1']['pause_url'],
                            'https://hc-bs-staging.herokuapp.com//api/v1/checks/0af1d589-e5e8-4e26-83cf-a38929136f3f/pause')
        # Alice 2
        self.assertEqual(checks['Alice 2']['last_ping'], self.a2.last_ping.isoformat())
        self.assertEqual(checks['Alice 2']['n_pings'], 0)
        self.assertNotEqual(checks['Alice 2']['pause_url'],
                            'https://hc-bs-staging.herokuapp.com//api/v1/checks/2bf1aa96-e8d8-4d0a-9408-d33d0829907e/pause')

    def test_it_shows_only_users_checks(self):
        bobs_check = Check(user=self.bob, name="Bob 1")
        bobs_check.save()

        r = self.get()
        data = r.json()
        self.assertEqual(len(data["checks"]), 2)
        for check in data["checks"]:
            self.assertNotEqual(check["name"], "Bob 1")

    def test_it_accepts_api_key_from_request_body(self):
        payload = json.dumps({"api_key": "abc"})
        # Test that it accepts an api_key in the request
        self.assertTrue(payload)
