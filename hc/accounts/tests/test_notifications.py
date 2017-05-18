from hc.test import BaseTestCase
from hc.accounts.models import MONTHLY_REPORTS, WEEKLY_REPORTS, DAILY_REPORTS


class NotificationsTestCase(BaseTestCase):

    def test_it_saves_reports_allowed_monthly(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"reports_allowed": 1}
        r = self.client.post("/accounts/profile/notifications/", form)
        assert r.status_code == 200

        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.reports_allowed, MONTHLY_REPORTS)

    def test_it_saves_reports_allowed_weekly(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"reports_allowed": 2}
        # import ipdb; ipdb.set_trace()
        r = self.client.post("/accounts/profile/notifications/", form)
        assert r.status_code == 200

        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.reports_allowed, WEEKLY_REPORTS)

    def test_it_saves_reports_allowed_daily(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"reports_allowed": 3}
        r = self.client.post("/accounts/profile/notifications/", form)
        assert r.status_code == 200

        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.reports_allowed, DAILY_REPORTS)

