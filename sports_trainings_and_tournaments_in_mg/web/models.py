import json
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    ROLE_CHOICES = (
        ('student', 'student'),
        ('teacher', 'teacher')
    )
    MAX_ROLE_LENGTH = max((len(r) for r, _ in ROLE_CHOICES))

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=MAX_ROLE_LENGTH,
        choices=ROLE_CHOICES
    )
    categories = models.ManyToManyField(
        'Category',
        through='ProfileCategory',
        related_name='profiles'
    )
    is_complete = models.BooleanField(
        default=False
    )
    absence_count = models.PositiveIntegerField(
        default=0
    )
    is_banned_from_participation = models.BooleanField(
        default=False
    )
    is_active = models.BooleanField(
        default=True
    )

    def add_absence(self):
        self.absence_count += 1

        if self.absence_count >= 5:
            self.is_banned_from_participation = True

        self.save(update_fields=['absence_count', 'is_banned_from_participation'])

        if self.is_banned_from_participation:
            self.remove_from_participation()

    def remove_from_participation(self):
        future_events = Event.objects.filter(date__gte=timezone.now().date())
        TeamMatchProfile.objects.filter(
            profile=self,
            team_match__matches__activity__events__in=future_events
        ).delete()

        TeamPermissionRequest.objects.filter(student=self, status='pending').delete()

        TeamPermissionRequest.objects.filter(student=self, status='approved').update(status='rejected')

    def reset_absence_ban(self):
        self.absence_count = 0
        self.is_banned_from_participation = False
        self.save(update_fields=['absence_count', 'is_banned_from_participation'])

    def __str__(self):
        return str(self.user.email)


class Grade(models.Model):
    GRADE_CHOICES = (
        (5, 5),
        (6, 6),
        (7, 7),
        (8, 8),
        (9, 9),
        (10, 10),
        (11, 11),
        (12, 12),
    )

    CLASS_LETTER_CHOICES = (
        ('А', 'А'),
        ('Б', 'Б'),
        ('В', 'В'),
        ('Г', 'Г'),
        ('Д', 'Д'),
        ('Е', 'Е'),
        ('Ж', 'Ж'),
        ('З', 'З'),
    )
    MAX_CLASS_LETTER_LENGTH = 1

    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='grade'
    )
    grade = models.PositiveIntegerField(
        choices=GRADE_CHOICES,
        null=True,
        blank=True
    )
    class_letter = models.CharField(
        max_length=MAX_CLASS_LETTER_LENGTH,
        choices=CLASS_LETTER_CHOICES,
        null=True,
        blank=True
    )
    last_promoted_year = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('grade', 'class_letter')

    def __str__(self):
        return f'{self.grade} "{self.class_letter}"'


class GradeActivity(models.Model):
    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE
    )
    activity = models.ForeignKey(
        'Activity',
        on_delete=models.CASCADE
    )


class Category(models.Model):
    CATEGORY_CHOICES = (
        ('football', 'футбол'),
        ('volleyball', 'волейбол'),
        ('basketball', 'баскетбол'),
        ('table tennis', 'тенис на маса'),
        ('running', 'бягане'),
        ('badminton', 'бадминтон')
    )
    MAX_CATEGORY_LENGTH = max(len(c) for c, _ in CATEGORY_CHOICES)

    category = models.CharField(
        max_length=MAX_CATEGORY_LENGTH,
        choices=CATEGORY_CHOICES,
        unique=True,
    )

    def __str__(self):
        translations = {
            'football': 'футбол',
            'volleyball': 'волейбол',
            'basketball': 'баскетбол',
            'table tennis': 'тенис на маса',
            'running': 'бягане',
            'badminton': 'бадминтон'
        }
        return translations.get(self.category.lower(), self.category)


class ProfileCategory(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ('profile', 'category')

    def clean(self):
        if self.profile.role != 'student':
            raise ValidationError('Само ученици могат да имат категории.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Achievement(models.Model):
    MAX_NAME_LENGTH = 30
    MIN_NAME_LENGTH = 2

    MAX_DESCRIPTION_LENGTH = 500
    MIN_DESCRIPTION_LENGTH = 5

    MAX_AWARD_LENGTH = 20
    MIN_AWARD_LENGTH = 2

    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        validators=(
            MinLengthValidator(MIN_NAME_LENGTH),
        )
    )
    description = models.TextField(
        max_length=MAX_DESCRIPTION_LENGTH,
        validators=(
            MinLengthValidator(MIN_DESCRIPTION_LENGTH),
        ),
        null=True,
        blank=True
    )
    award = models.CharField(
        max_length=MAX_AWARD_LENGTH,
        validators=(
            MinLengthValidator(MIN_AWARD_LENGTH),
        )
    )

    def __str__(self):
        return self.name


class Team(models.Model):
    MAX_NAME_LENGTH = 30

    name = models.CharField(
        max_length=MAX_NAME_LENGTH
    )
    number_of_players = models.PositiveIntegerField()
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='teams'
    )
    grades = models.ManyToManyField(
        Grade,
        through='GradeTeam',
        related_name='teams',
        blank=True
    )
    achievements = models.ManyToManyField(
        Achievement,
        through='TeamAchievement',
        related_name='teams'
    )
    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.name


class GradeTeam(models.Model):
    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('grade', 'team')


class TeamAchievement(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('team', 'achievement')


class Match(models.Model):
    SCORE_CATEGORIES = {'football', 'basketball', 'volleyball', 'table tennis', 'badminton'}
    PLACEMENT_CATEGORIES = {'running'}

    MAX_LABEL_LENGTH = 20

    label = models.CharField(
        max_length=MAX_LABEL_LENGTH,
        null=True,
        blank=True
    )
    teams = models.ManyToManyField(
        Team,
        through='TeamMatch',
        related_name='matches',
        blank=True
    )
    activity = models.ForeignKey(
        'Activity',
        on_delete=models.PROTECT,
        related_name='matches',
        null=False,
        blank=False
    )
    max_teams_per_match = models.PositiveIntegerField(
        default=2,
        blank=True
    )
    start_time = models.DateTimeField()
    duration = models.PositiveIntegerField()
    result = models.JSONField(
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        if self.label:
            return f'{self.label} - {self.activity}'

        return f'{self.activity} - {self.start_time}'

    def end_time(self):
        return self.start_time + timedelta(minutes=self.duration)

    def is_finished(self):
        return timezone.now() >= self.end_time()

    def clean(self):
        super().clean()

        if not self.pk:
            return

        if not self.result:
            if self.is_finished():
                raise ValidationError('Приключили мачове трябва да имат резултат.')
            return

        category = self.activity.category.category.lower()
        team_ids = set(self.teams.values_list('id', flat=True))

        if category in self.SCORE_CATEGORIES:
            scores = self.result.get('scores')
            if not isinstance(scores, dict):
                raise ValidationError('Scores must be provided.')

            score_team_ids = {int(k) for k in scores.keys()}
            if score_team_ids != team_ids:
                raise ValidationError('Резултатите трябва да включват всички участващи отбори.')

            for value in scores.values():
                if not isinstance(value, int) or value < 0:
                    raise ValidationError('Резултите трябва да са неотрицателни числа')

        elif category in self.PLACEMENT_CATEGORIES:
            placements = self.result.get('placements')
            if not isinstance(placements, list):
                raise ValidationError('Резултатите от съзтезанието трябва да включва позициите.')

            placement_team_ids = {p['team_id'] for p in placements}
            if placement_team_ids != team_ids:
                raise ValidationError('Позициите трябва да съдържат само един отбор')

    def winners(self):
        if not self.result:
            return Team.objects.none()

        result = self.result

        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                return Team.objects.none()

        category = self.activity.category.category.lower()

        if category in self.SCORE_CATEGORIES:
            scores = result.get('scores') or {}
            if not scores:
                return Team.objects.none()

            max_score = max(scores.values())
            return Team.objects.filter(id__in=[
                int(tid) for tid, s in scores.items() if s == max_score
            ])

        if category in self.PLACEMENT_CATEGORIES:
            placements = result.get('placements') or []
            if not placements:
                return Team.objects.none()

            first = min(placements, key=lambda x: x['value'])
            return Team.objects.filter(id=first['team_id'])

        return Team.objects.none()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TeamMatch(models.Model):
    STATUS_CHOICES = (
        ('editing', 'редактира се'),
        ('locked', 'заключен'),
    )
    MAX_STATUS_LENGTH = max(len(s) for s, _ in STATUS_CHOICES)

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE
    )
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='team_matches'
    )

    status = models.CharField(
        max_length=MAX_STATUS_LENGTH,
        choices=STATUS_CHOICES,
        default='editing'
    )
    students = models.ManyToManyField(
        Profile,
        through='TeamMatchProfile',
        related_name='student_team_matches',
        blank=True
    )

    class Meta:
        unique_together = ('team', 'match')

    def is_full(self):
        return self.students.count() >= self.team.number_of_players

    def can_student_request(self, profile):
        if profile.role != 'student':
            return False

        if self.team.requests.filter(student=profile, status='pending').exists():
            return False

        if self.students.filter(user=profile.user).exists():
            return False

        return True

    def can_student_cancel_request(self, profile):
        return self.team.requests.filter(student=profile, status='pending').exists()

    def can_student_leave(self, profile):
        return self.students.filter(pk=profile.pk).exists()

    def clean(self):
        if not self.match_id:
            return

        current_count = TeamMatch.objects.filter(match=self.match).count()

        if not self.pk and current_count >= self.match.max_teams_per_match:
            raise ValidationError(
                f'Максимално {self.match.max_teams_per_match} отбори са позволени за този мач.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TeamMatchProfile(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )
    team_match = models.ForeignKey(
        TeamMatch,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('profile', 'team_match')


class Activity(models.Model):
    MAX_NAME_LENGTH = 30
    MIN_NAME_LENGTH = 2

    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        validators=(
            MinLengthValidator(MIN_NAME_LENGTH),
        )
    )
    date = models.DateTimeField()
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    grades = models.ManyToManyField(
        Grade,
        through=GradeActivity,
        related_name='activities',
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.name

    def allows_team(self, team):
        activity_grades = self.grades.all()

        if not activity_grades.exists():
            return True

        return not team.grades.exclude(
            id__in=activity_grades.values_list("id", flat=True)
        ).exists()


class Event(models.Model):
    MAX_NAME_LENGTH = 30
    MIN_NAME_LENGTH = 2

    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        validators=(
            MinLengthValidator(MIN_NAME_LENGTH),
        )
    )
    students = models.ManyToManyField(
        Profile,
        through='ProfileEvent',
        related_name='events',
        blank=True
    )
    date = models.DateTimeField()
    activities = models.ManyToManyField(
        Activity,
        through='ActivityEvent',
        related_name='events'
    )
    achievements = models.ManyToManyField(
        Achievement,
        through='EventAchievement',
        related_name='events'
    )
    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.name


class ActivityEvent(models.Model):
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE
    )


class ProfileEvent(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='profiles'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='events'
    )

    class Meta:
        unique_together = ('profile', 'event')

    def clean(self):
        if self.profile.role != 'student':
            raise ValidationError('Само ученици могат да участват в събития.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class EventAchievement(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('event', 'achievement')


class TeamPermissionRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'чакащ'),
        ('approved', 'одобрен'),
        ('rejected', 'отхвърлен')
    )
    MAX_STATUS_LENGTH = max((len(s) for s, _ in STATUS_CHOICES))

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='requests'
    )
    team_match = models.ForeignKey(
        TeamMatch,
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='team_requests'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='event_requests'
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True
    )
    status = models.CharField(
        max_length=MAX_STATUS_LENGTH,
        choices=STATUS_CHOICES,
        default='pending'
    )

    class Meta:
        unique_together = ('team', 'student')


class Notification(models.Model):
    MAX_TITLE_LENGTH = 150

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(
        max_length=MAX_TITLE_LENGTH
    )
    message = models.TextField()
    is_read = models.BooleanField(
        default=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
