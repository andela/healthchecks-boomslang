import base64
import os
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core import signing
from django.db import models
from django.urls import reverse
from django.utils import timezone
from hc.lib import emails

MONTHLY_REPORTS = 1
WEEKLY_REPORTS = 2
DAILY_REPORTS = 3

class ProfileManager(models.Manager):
    def for_user(self, user):
        profile = self.filter(user=user).first()
        if profile is None:
            profile = Profile(user=user, team_access_allowed=user.is_superuser)
            profile.save()
        return profile


class Profile(models.Model):
    # Owner:
    user = models.OneToOneField(User, blank=True, null=True)
    team_name = models.CharField(max_length=200, blank=True)
    team_access_allowed = models.BooleanField(default=False)
    next_report_date = models.DateTimeField(null=True, blank=True)
    reports_allowed = models.IntegerField(default=1)
    ping_log_limit = models.IntegerField(default=100)
    token = models.CharField(max_length=128, blank=True)
    api_key = models.CharField(max_length=128, blank=True)
    current_team = models.ForeignKey("self", null=True)

    objects = ProfileManager()

    def __str__(self):
        return self.team_name or self.user.email

    def send_instant_login_link(self, inviting_profile=None):
        token = str(uuid.uuid4())
        self.token = make_password(token)
        self.save()

        path = reverse("hc-check-token", args=[self.user.username, token])
        ctx = {
            "button_text": "Log In",
            "button_url": settings.SITE_ROOT + path,
            "inviting_profile": inviting_profile
        }
        emails.login(self.user.email, ctx)

    def send_set_password_link(self):
        token = str(uuid.uuid4())
        self.token = make_password(token)
        self.save()

        path = reverse("hc-set-password", args=[token])
        ctx = {
            "button_text": "Set Password",
            "button_url": settings.SITE_ROOT + path
        }
        emails.set_password(self.user.email, ctx)

    def set_api_key(self):
        self.api_key = base64.urlsafe_b64encode(os.urandom(24))
        self.save()

    def send_report(self):
        # reset next report date first:
        report_date = ''
        now = timezone.now()
        if self.reports_allowed == MONTHLY_REPORTS:
            self.next_report_date = now + timedelta(days=30)
            report_date += "Monthly"

        elif self.reports_allowed == WEEKLY_REPORTS:
            self.next_report_date = now + timedelta(days=7)
            report_date += "Weekly"

        elif self.reports_allowed == DAILY_REPORTS:
            self.next_report_date = now + timedelta(days=1)
            report_date += "Daily"
        self.save()

        if self.reports_allowed:
            token = signing.Signer().sign(uuid.uuid4())
            path = reverse("hc-unsubscribe-reports", args=[self.user.username])
            unsub_link = "%s%s?token=%s" % (settings.SITE_ROOT, path, token)

            ctx = {
                "checks": self.user.check_set.order_by("created"),
                "now": now,
                "unsub_link": unsub_link,
                "report_date": report_date

                }

            emails.report(self.user.email, ctx)

    def invite(self, user):
        member = Member(team=self, user=user)
        member.save()

        # Switch the invited user over to the new team so they
        # notice the new team on next visit:
        user.profile.current_team = self
        user.profile.save()

        user.profile.send_instant_login_link(self)


class Member(models.Model):
    team = models.ForeignKey(Profile)
    user = models.ForeignKey(User)
