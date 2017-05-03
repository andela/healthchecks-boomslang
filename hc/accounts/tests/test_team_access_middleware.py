from django.contrib.auth.models import User
from django.test import TestCase
from hc.accounts.models import Profile


class TeamAccessMiddlewareTestCase(TestCase):

    def test_it_handles_missing_profile(self):
        count_before = Profile.objects.count()
        user = User(username="ned", email="ned@example.org")
        user.set_password("password")
        user.save()

        self.client.login(username="ned@example.org", password="password")
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)

        ### Assert the new Profile objects count
        count_after = Profile.objects.count()
        self.assertEqual(count_after,count_before + 1)
