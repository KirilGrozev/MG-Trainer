from django import forms
from django.core.exceptions import ValidationError

from sports_trainings_and_tournaments_in_mg.web.models import Category, Profile, Achievement, Activity, Event, Grade, \
    Team, Match


class EditStudentInfoForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Profile
        fields = ('categories',)


class EditGradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ('grade', 'class_letter')

        widgets = {
            'grade': forms.Select(attrs={'placeholder': 'Enter Grade'}),
            'class_letter': forms.Select(attrs={'placeholder': 'Enter Class Letter'})
        }

        labels = {
            'grade': 'Grade',
            'class_letter': 'Class Letter'
        }


class CreateAchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = '__all__'

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter Name'}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 70, 'placeholder': 'Enter Description'}),
            'award': forms.TextInput(attrs={'placeholder': 'Enter Prize'}),
        }

        labels = {
            'name': 'Name',
            'description': 'Description',
            'award': 'Prize',
        }


class CreateMatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ('label', 'max_teams_per_match', 'start_time', 'duration')

        widgets = {
            'label': forms.TextInput(attrs={'placeholder': 'Enter Label'}),
            'max_teams_per_match': forms.NumberInput(attrs={'placeholder': 'Enter Max Teams Per Match'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': 'Enter Start Time'}),
            'duration': forms.NumberInput(attrs={'placeholder': 'Enter Duration'})
        }

        labels = {
            'label': 'Label',
            'max_teams_per_match': 'Max Teams Per Team',
            'start_time': 'Start Time',
            'duration': 'Duration'
        }


class EditMatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ('label', 'start_time', 'duration')

    labels = {
        'label': 'Label',
        'start_time': 'Start Time',
        'duration': 'Duration'
    }


class CreateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('name', 'number_of_players', 'grades')

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter Name'}),
            'numbers_of_players': forms.NumberInput(attrs={'placeholder': 'Enter Number Of Players'}),
            'grades': forms.CheckboxSelectMultiple(attrs={'placeholder': 'Choose Available Grades'}),
        }

        labels = {
            'name': 'Name',
            'numbers_of_players': 'Number Of Players',
            'grades': 'Grades'
        }

    def __init__(self, *args, activity=None, **kwargs):
        super().__init__(*args, **kwargs)

        if activity and activity.grades.exists():
            self.fields['grades'].queryset = activity.grades.all()
            self.fields['grades'].required = True
        else:
            self.fields['grades'].queryset = Grade.objects.all()
            self.fields['grades'].required = False


class CreateActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        exclude = ('is_active', 'events')

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter Name'}),
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': 'Enter A Date'}),
            'category': forms.Select(attrs={'placeholder': 'Choose Category'}),
            'grades': forms.CheckboxSelectMultiple(attrs={'placeholder': 'Choose Available Grades'}),
        }

        labels = {
            'name': 'Name',
            'date': 'Date',
            'category': 'Category',
            'grades': 'Grades'
        }


class EditActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ('name', 'date', 'grades')

        labels = {
            'name': 'Name',
            'date': 'Date',
            'grades': 'Grades'
        }


class CreateEventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ('name', 'date')

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter Name'}),
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': 'Enter The Event Date'}),
        }

        labels = {
            'name': 'Name',
            'date': 'Event Date',
        }


class ScoreResultForm(forms.Form):
    def __init__(self, *args, match=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.match = match
        self.teams = list(match.teams.all())

        if len(self.teams) < 2:
            raise ValidationError('A score result requires at least 2 teams.')

        existing_scores = {}
        if isinstance(match.result, dict):
            existing_scores = match.result.get('scores', {})

        for team in self.teams:
            self.fields[f'team_{team.id}'] = forms.IntegerField(
                min_value=0,
                required=True,
                label=team.name,
                initial=existing_scores.get(str(team.id))
            )

    def to_result_json(self):
        return {
            'scores': {
                str(team.id): self.cleaned_data[f'team_{team.id}']
                for team in self.teams
            }
        }


class RaceResultForm(forms.Form):
    def __init__(self, *args, match=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.match = match
        self.teams = list(match.teams.all())

        if len(self.teams) < 2:
            raise ValidationError('A race result requires at least 2 teams.')

        existing_placements = {}
        if isinstance(match.result, dict):
            placements = match.result.get('placements', [])
            existing_placements = {
                p['team_id']: p['value']
                for p in placements
                if isinstance(p, dict) and 'team_id' in p and 'value' in p
            }

        for team in self.teams:
            self.fields[f'team_{team.id}'] = forms.IntegerField(
                min_value=1,
                required=True,
                label=team.name,
                initial=existing_placements.get(team.id)
            )

    def clean(self):
        cleaned = super().clean()
        values = []

        for team in self.teams:
            value = cleaned.get(f'team_{team.id}')
            if value is not None:
                values.append(value)

        if len(values) != len(set(values)):
            raise forms.ValidationError('Placements must be unique.')

        return cleaned

    def to_result_json(self):
        placements = []
        for team in self.teams:
            placements.append({
                "team_id": team.id,
                "value": self.cleaned_data[f"team_{team.id}"]
            })

        placements.sort(key=lambda x: x["value"])

        return {
            "placements": placements
        }



