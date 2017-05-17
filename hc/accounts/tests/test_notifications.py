from hc.test import BaseTestCase


class NotificationsTestCase(BaseTestCase):

    def test_it_saves_reports_allowed_monthly(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"reports_allowed": "monthly_checked"}
        r = self.client.post("/accounts/profile/notifications/", form)
        assert r.status_code == 200

        self.alice.profile.refresh_from_db()
        self.assertTrue(self.alice.profile.reports_allowed)

    def test_it_saves_reports_allowed_weekly(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"reports_allowed": "weekly_checked"}
        r = self.client.post("/accounts/profile/notifications/", form)
        assert r.status_code == 200

        self.alice.profile.refresh_from_db()
        self.assertTrue(self.alice.profile.reports_allowed)

    def test_it_saves_reports_allowed_daily(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"reports_allowed": "daily_checked"}
        r = self.client.post("/accounts/profile/notifications/", form)
        assert r.status_code == 200

        self.alice.profile.refresh_from_db()
        self.assertTrue(self.alice.profile.reports_allowed)

