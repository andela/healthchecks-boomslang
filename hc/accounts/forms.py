from django import forms
from models import MONTHLY_REPORTS, WEEKLY_REPORTS, DAILY_REPORTS


class LowercaseEmailField(forms.EmailField):

    def clean(self, value):
        value = super(LowercaseEmailField, self).clean(value)
        return value.lower()


class EmailPasswordForm(forms.Form):
    email = LowercaseEmailField()
    password = forms.CharField(required=False)


class ReportSettingsForm(forms.Form):
    REPORT_CHOICES = (
        (MONTHLY_REPORTS, 'Each month send me a summary of my checks'),
        (WEEKLY_REPORTS, 'Each week send me a summary of my checks'),
        (DAILY_REPORTS, 'Each day send me a summary of my checks'),)
    reports_allowed = forms.ChoiceField(
        widget=forms.RadioSelect, choices=REPORT_CHOICES)


class SetPasswordForm(forms.Form):
    password = forms.CharField()


class InviteTeamMemberForm(forms.Form):
    email = LowercaseEmailField()


class RemoveTeamMemberForm(forms.Form):
    email = LowercaseEmailField()


class TeamNameForm(forms.Form):
    team_name = forms.CharField(max_length=200, required=True)
