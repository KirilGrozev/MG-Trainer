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
            'grade': forms.Select(attrs={'placeholder': 'Въведи клас'}),
            'class_letter': forms.Select(attrs={'placeholder': 'Въведи паралелка'})
        }

        labels = {
            'grade': 'Клас',
            'class_letter': 'Паралелка'
        }


class CreateAchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = '__all__'

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Въведи име'}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 70, 'placeholder': 'Въведи описание'}),
            'award': forms.TextInput(attrs={'placeholder': 'Въведи награда'}),
        }

        labels = {
            'name': 'Име',
            'description': 'Описание',
            'award': 'Награда',
        }


class CreateMatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ('label', 'max_teams_per_match', 'start_time', 'duration')

        widgets = {
            'label': forms.TextInput(attrs={'placeholder': 'Въведи наименование'}),
            'max_teams_per_match': forms.NumberInput(attrs={'placeholder': 'Въведи максимален брой отбори'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': 'Въведи начален час'}),
            'duration': forms.NumberInput(attrs={'placeholder': 'Въведи времетраене'})
        }

        labels = {
            'label': 'Наименование',
            'max_teams_per_match': 'Максимален брой отбори  ',
            'start_time': 'Начален час',
            'duration': 'Времетраене'
        }


class EditMatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ('label', 'start_time', 'duration')

    labels = {
        'label': 'Наименование',
        'start_time': 'Начален час',
        'duration': 'Времетраене'
    }


class CreateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('name', 'number_of_players', 'grades')

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Въведи име'}),
            'numbers_of_players': forms.NumberInput(attrs={'placeholder': 'Въведи брой играчи'}),
            'grades': forms.CheckboxSelectMultiple(attrs={'placeholder': 'Избери класове'}),
        }

        labels = {
            'name': 'Име',
            'numbers_of_players': 'Брой играчи',
            'grades': 'Класове'
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
            'name': forms.TextInput(attrs={'placeholder': 'Въведи име'}),
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': 'Въведи дата'}),
            'category': forms.Select(attrs={'placeholder': 'Избери категория'}),
            'grades': forms.CheckboxSelectMultiple(attrs={'placeholder': 'Избери класове'}),
        }

        labels = {
            'name': 'Име',
            'date': 'Дата',
            'category': 'Категория',
            'grades': 'Класове'
        }


class EditActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ('name', 'date', 'grades')

        labels = {
            'name': 'Име',
            'date': 'Дата',
            'grades': 'Класове'
        }


class CreateEventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ('name', 'date')

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Въведи име'}),
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': 'Въведи дата'}),
        }

        labels = {
            'name': 'Име',
            'date': 'Дата',
        }


class ScoreResultForm(forms.Form):
    def __init__(self, *args, match=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.match = match
        self.teams = list(match.teams.all())

        if len(self.teams) < 2:
            raise ValidationError('За резултат трябват поне 2 отбора!')

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
            raise ValidationError('За резултат трябват поне 2 отбора!')

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
            raise forms.ValidationError('Класирането трябва да е уникално')

        return cleaned

    def to_result_json(self):
        placements = []
        for team in self.teams:
            placements.append({
                'team_id': team.id,
                'value': self.cleaned_data[f'team_{team.id}']
            })

        placements.sort(key=lambda x: x['value'])

        return {
            'placements': placements
        }



