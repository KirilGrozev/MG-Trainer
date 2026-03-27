import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Q
from django.http import JsonResponse

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView, UpdateView, ListView, CreateView, DetailView

from sports_trainings_and_tournaments_in_mg.web.forms import CreateActivityForm, \
    CreateAchievementForm, CreateEventForm, EditStudentInfoForm, EditGradeForm, CreateTeamForm, \
    CreateMatchForm, EditActivityForm, ScoreResultForm, RaceResultForm, EditMatchForm
from sports_trainings_and_tournaments_in_mg.web.mixins import NoPermissionRedirectMixin
from sports_trainings_and_tournaments_in_mg.web.models import Event, Profile, Activity, Achievement, Grade, Match, \
    Team, TeamMatch, TeamPermissionRequest, ActivityEvent, EventAchievement, TeamAchievement, \
    TeamMatchProfile

from allauth.socialaccount.providers.google.views import oauth2_login


#class GoogleLoginRedirectView(View):
#   def get(self, request, *args, **kwargs):
#      return oauth2_login(request)


class DashboardRedirect(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')

        profile = request.user.profile

        if profile.role == 'teacher':
            return redirect('teacher dashboard')

        if not profile.is_complete:
            return redirect('additional info')

        return redirect('student dashboard')


class AdditionalStudentInfo(LoginRequiredMixin, NoPermissionRedirectMixin, UserPassesTestMixin, TemplateView):
    template_name = 'additional_student_info.html'

    def test_func(self):
        return self.request.user.profile.role == 'student'

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_forms(self):
        profile = self.request.user.profile
        grade_obj, _ = Grade.objects.get_or_create(profile=profile)

        if self.request.method == 'POST':
            profile_form = EditStudentInfoForm(self.request.POST, instance=profile, prefix='profile')
            grade_form = EditGradeForm(self.request.POST, instance=grade_obj, prefix='grade')
        else:
            profile_form = EditStudentInfoForm(instance=profile, prefix='profile')
            grade_form = EditGradeForm(instance=grade_obj, prefix='grade')

        return profile_form, grade_form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile_form, grade_form = self.get_forms()
        ctx['profile_form'] = profile_form
        ctx['grade_form'] = grade_form
        return ctx

    def post(self, request, *args, **kwargs):
        profile_form, grade_form = self.get_forms()

        if profile_form.is_valid() and grade_form.is_valid():
            profile_form.save()
            grade_form.save()

            profile = request.user.profile
            profile.is_complete = True
            profile.save(update_fields=['is_complete'])

            return redirect('student dashboard')

        context = self.get_context_data()
        context['profile_form'] = profile_form
        context['grade_form'] = grade_form
        return self.render_to_response(context)


class EditStudentCategories(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    template_name = 'edit_student_categories.html'
    form_class = EditStudentInfoForm
    success_url = reverse_lazy('student dashboard')

    def test_func(self):
        return self.request.user.profile.role == 'student'

    def get_object(self, queryset=None):
        return self.request.user.profile


class StudentDashboard(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'student_dashboard.html'

    def test_func(self):
        return self.request.user.profile.role == 'student'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile

        if not profile.is_active:
            context['my_request'] = TeamPermissionRequest.objects.none()
            context['my_teams'] = TeamMatch.objects.none()

        context['notifications'] = profile.notifications.order_by('-created_at')[:10]

        context['events'] = Event.objects\
            .filter(is_active=True, activities__category__in=profile.categories.all())\
            .distinct()\
            .order_by('date')

        context['my_request'] = TeamPermissionRequest.objects\
            .filter(student=profile)

        context['my_teams'] = profile.student_team_matches.all()

        #context['upcoming_matches'] = (
        #    Match.objects
        #    .filter(
        #        teams__students=profile,
        #        start_time__gte=timezone.now()
        #    )
        #    .distinct()
        #    .order_by('start_time')
        #)

        context['my_achievements'] = (
            Achievement.objects.filter(teams__teammatch__teammatchprofile__profile=profile)
            .distinct()
            .order_by('name')
        )

        return context


class TeacherDashboard(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'teacher_dashboard.html'
    context_object_name = 'students'

    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def get_queryset(self):
        q = self.request.GET.get('q', '').strip()

        queryset = (
            Profile.objects
            .filter(role='student', is_active=True)
            .select_related('user')
            .order_by('-absence_count', 'user__email')
        )

        if q:
            queryset = queryset.filter(
                Q(user__email__icontains=q)
            )
        else:
            queryset = queryset[:5]

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['q'] = self.request.GET.get('q', '').strip()
        context['events'] = Event.objects.filter(is_active=True).order_by('date')

        return context


@login_required
@require_GET
def student_email_suggestions(request):
    if request.user.profile.role != 'teacher':
        return JsonResponse([], safe=False)

    q = request.GET.get('q', '').strip()

    if not q:
        return JsonResponse([], safe=False)

    students = (
        Profile.objects
        .filter(role='student', is_active=True, user__email__icontains=q)
        .select_related('user')
        .order_by('user__email')[:8]
    )

    data = [
        {
            'id': student.id,
            'email': student.user.email,
            'absence_count': student.absence_count,
            'is_banned': student.is_banned_from_participation,
        }
        for student in students
    ]

    return JsonResponse(data, safe=False)


class CreateActivity(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'create_activity.html'
    model = Activity
    form_class = CreateActivityForm

    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=kwargs['event_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        return context

    def form_valid(self, form):
        activity = form.save()

        try:
            ActivityEvent.objects.create(event=self.event, activity=activity)
        except ValidationError:
            activity.delete()
            return self.form_invalid(form)

        return redirect('event details', pk=self.event.pk)


class EditActivity(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = 'edit_activity.html'
    model = Activity
    form_class = EditActivityForm
    success_url = reverse_lazy('activity details')

    def test_func(self):
        return self.request.user.profile.role == 'teacher'


class ArchiveActivity(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, pk):
        activity = get_object_or_404(Activity, pk=pk)
        event_id = request.POST.get('event_id')
        event = get_object_or_404(Event, pk=event_id)

        if activity.matches.exists():
            activity.is_active = False
            activity.save(update_fields=['is_active'])
            return redirect('event details', pk=event.pk)

        if ActivityEvent.objects.filter(activity=activity).count() > 1:
            ActivityEvent.objects.filter(activity=activity, event=event).delete()
            return redirect('event details', pk=event.pk)

        ActivityEvent.objects.filter(activity=activity, event=event).delete()
        activity.delete()
        return redirect('event details', pk=event.pk)


class ActivityDetails(LoginRequiredMixin, DetailView):
    template_name = 'activity_details.html'
    queryset = Activity.objects.prefetch_related('matches')
    context_object_name = 'activity'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activity = self.object

        event = get_object_or_404(Event, pk=self.kwargs['event_id'])

        context['event'] = event

        context['active_matches_count'] = activity.matches.filter(is_active=True).count()

        context['match_actions'] = {}
        for m in activity.matches.all():
            if m.result:
                context['match_actions'][m.id] = 'Архивирай мач'
            else:
                context['match_actions'][m.id] = 'Изтрий мач'

        return context


class CreateMatch(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'create_match.html'
    model = Match
    form_class = CreateMatchForm

    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def dispatch(self, request, *args, **kwargs):
        self.activity = get_object_or_404(Activity, pk=kwargs['activity_id'])
        self.event_id = request.GET.get('event_id') or request.POST.get('event_id')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity'] = self.activity
        context['event_id'] = self.event_id
        return context

    def form_valid(self, form):
        match = form.save(commit=False)
        match.activity = self.activity
        match.save()

        event_id = self.request.POST.get('event_id')

        return redirect('activity details', event_id=event_id, pk=self.activity.pk)


class EditMatch(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = 'edit_match.html'
    model = Match
    form_class = EditMatchForm
    success_url = reverse_lazy('match details')

    def test_func(self):
        return self.request.user.profile.role == 'teacher'


class ArchiveMatch(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, pk):
        match = get_object_or_404(Match, pk=pk)
        activity_id = match.activity.pk
        event_id = request.POST.get('event_id')

        if match.result:
            match.is_active = False
            match.save(update_fields=['is_active'])
            return redirect('activity details', event_id=event_id, pk=activity_id)

        match.delete()
        return redirect('activity details', event_id=event_id, pk=activity_id)


class MatchDetails(LoginRequiredMixin, DetailView):
    template_name = 'match_details.html'
    queryset = Match.objects.prefetch_related('team_matches__students')
    context_object_name = 'match'

    def get_result_form_class(self, match):
        score_categories = {'football', 'basketball', 'volleyball', 'table tennis', 'badminton'}
        placement_category = {'running'}

        kind = match.activity.category.category.lower()
        if kind in score_categories:
            return ScoreResultForm
        if kind in placement_category:
            return RaceResultForm
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.object
        profile = self.request.user.profile
        event = get_object_or_404(Event, pk=self.kwargs['event_id'])

        already_in = match.teams.values_list('id', flat=True)

        allowed_grades = match.activity.grades.all()

        available_teams = (Team.objects.filter(is_active=True, category=match.activity.category) \
            .exclude(id__in=already_in).distinct())

        if allowed_grades.exists():
            available_teams = available_teams.filter(
                grades__in=allowed_grades
            )

        context['event'] = event

        context['available_teams'] = available_teams

        context['team_actions'] = {}

        for team in match.teams.filter(is_active=True):
            team_match = get_object_or_404(TeamMatch, team=team, match=match)
            if team_match.can_student_request(profile):
                context['team_actions'][team_match.id] = 'join'
            elif team_match.can_student_cancel_request(profile):
                context['team_actions'][team_match.id] = 'cancel'
            elif team_match.can_student_leave(profile):
                context['team_actions'][team_match.id] = 'leave'

        if profile.role != 'student' or not profile.is_active:
            context['team_actions'] = {}

        context['available_achievements'] = Achievement.objects.filter(events=event)\
            .distinct()\
            .order_by('name')

        if match.teams.count() >= 2:
            FormClass = self.get_result_form_class(match)
            context['result_form'] = FormClass(match=match) if FormClass else None

        teams = match.teams.filter(is_active=True)
        context['team_lookup'] = {
            team.id: team.name
            for team in teams
        }

        return context


class MatchResultView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def get_form_class(self, match: Match):
        score_categories = {'football', 'basketball', 'volleyball', 'table tennis', 'badminton'}
        placement_category = {'running'}

        kind = match.activity.category.category.lower()
        if kind in score_categories:
            return ScoreResultForm
        if kind in placement_category:
            return RaceResultForm
        raise ValueError('Unsupported category for results')

    def post(self, request, pk):
        match = get_object_or_404(Match, pk=pk)
        event_id = request.POST.get('event_id')

        if not match.is_finished():
            messages.error(request, 'Мачът не е приключил.')
            return redirect('match details', event_id=event_id, pk=match.pk)

        FormClass = self.get_form_class(match)
        form = FormClass(request.POST, match=match)

        if form.is_valid():
            match.result = form.to_result_json()
            match.full_clean()
            match.save(update_fields=['result'])

        return redirect('match details', event_id=event_id, pk=match.pk)


class CreateTeam(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'create_team.html'
    model = Team
    form_class = CreateTeamForm

    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def dispatch(self, request, *args, **kwargs):
        self.match = get_object_or_404(Match, pk=kwargs['match_id'])
        self.event_id = request.GET.get('event_id') or request.POST.get('event_id')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['match'] = self.match
        context['event_id'] = self.event_id
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['activity'] = self.match.activity
        return kwargs

    def form_valid(self, form):
        team = form.save(commit=False)
        team.category = self.match.activity.category
        team.save()
        event_id = self.request.POST.get('event_id')

        if not self.match.activity.allows_team(team):
            form.add_error('grades', 'Избраните класове не са позволени за тази дейност.')
            team.delete()
            return self.form_invalid(form)

        try:
            TeamMatch.objects.create(match=self.match, team=team)
        except ValidationError:
            team.delete()
            return self.form_invalid(form)

        return redirect('match details', event_id=event_id, pk=self.match.pk)


class AddExistingTeam(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, pk):
        match = get_object_or_404(Match, pk=pk)
        team_id = request.POST.get('team_id')
        event_id = request.POST.get('event_id')

        if not team_id:
            return redirect('match details', event_id=event_id, pk=match.pk)

        team = get_object_or_404(Team, pk=team_id)

        if not match.activity.allows_team(team):
            messages.error(request, 'Този отбор не отговаря на ограниченията за класове на дейността.')
            return redirect('match details', event_id=event_id, pk=match.pk)

        try:
            TeamMatch.objects.create(match=match, team=team)
        except ValidationError:
            pass

        return redirect('match details', event_id=event_id, pk=match.pk)


class RemoveTeam(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        match_id = request.POST.get('match_id')
        match = get_object_or_404(Match, pk=match_id)
        event_id = request.POST.get('event_id')

        if match.result or match.is_finished():
            messages.error(request, 'Мачът няма резултат.')
            return redirect('match details', event_id=event_id, pk=match.pk)

        TeamMatch.objects.filter(match=match, team=team).delete()

        return redirect('match details', event_id=event_id, pk=match.pk)


class ArchiveTeam(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        match_id = request.POST.get('match_id')
        event_id = request.POST.get('event_id')
        match = get_object_or_404(Match, pk=match_id)
        team_match = get_object_or_404(TeamMatch, match=match, team=team)

        if match.result or match.is_finished():
            return redirect('match details', event_id=event_id, pk=match.pk)

        if team_match.students.exists():
            team.is_active = False
            team.save(update_fields=['is_active'])
            redirect('match details', event_id=event_id, pk=match.pk)

        TeamMatch.objects.filter(team=team, match=match)
        team.delete()
        return redirect('match details', event_id=event_id, pk=match.pk)


class RemoveStudent(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, pk):
        profile_id = request.POST.get('profile_id')
        team = get_object_or_404(Team, pk=pk)
        match_id = request.POST.get('match_id')
        event_id = request.POST.get('event_id')
        match = get_object_or_404(Match, pk=match_id)
        team_match = get_object_or_404(TeamMatch, match=match, team=team)

        if match.result or match.is_finished():
            messages.error(request, 'Мачът няма резултат.')
            return redirect('match details', event_id=event_id, pk=match.pk)

        TeamMatchProfile.objects.filter(team_match=team_match, profile_id=profile_id).delete()
        return redirect('match details', event_id=event_id, pk=match.id)


class CreateAchievement(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'create_achievement.html'
    model = Achievement
    form_class = CreateAchievementForm
    success_url = reverse_lazy('teacher dashboard')

    def test_func(self):
        return self.request.user.profile.role == 'teacher'


class AddEventAchievement(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        achievement_id = request.POST.get('achievement_id')

        if not achievement_id:
            return redirect('event details', pk=event.pk)

        achievement = get_object_or_404(Achievement, pk=achievement_id)

        try:
            EventAchievement.objects.create(event=event, achievement=achievement)
        except ValidationError:
            pass

        return redirect('event details', pk=event.pk)


class AddTeamAchievement(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        match_id = request.POST.get('match_id')
        achievement_id = request.POST.get('achievement_id')

        event_id = request.POST.get('event_id')

        if not achievement_id:
            return redirect('match details', event_id=event_id, pk=match_id)

        achievement = get_object_or_404(Achievement, pk=achievement_id)

        if not achievement.events.filter(pk=event_id).exists():
            return redirect('match details', event_id=event_id, pk=match_id)

        try:
            TeamAchievement.objects.create(team=team, achievement=achievement)
        except ValidationError:
            pass

        return redirect('match details', event_id=event_id, pk=match_id)


class CreateEvent(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'create_event.html'
    model = Event
    form_class = CreateEventForm
    success_url = reverse_lazy('teacher dashboard')

    def test_func(self):
        return self.request.user.profile.role == 'teacher'


class EditEvent(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        new_name = request.POST.get('name', '').strip()

        if new_name:
            event.name = new_name
            event.save(update_fields=['name'])

        return redirect('event details', event.pk)


class ArchiveEvent(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)

        if event.activities.exists():
            event.is_active = False
            event.save(update_fields=['is_active'])
            return redirect('teacher dashboard')

        event.delete()
        return redirect('teacher dashboard')

    def test_func(self):
        return self.request.user.profile.role == 'teacher'


class EventDetails(LoginRequiredMixin, DetailView):
    template_name = 'event_details.html'
    queryset = Event.objects.prefetch_related('activities')
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object

        context['available_achievements'] = Achievement.objects\
            .exclude(id__in=event.achievements.values_list('id', flat=True))

        context['active_activities_count'] = event.activities.filter(is_active=True).count()

        context['activity_action'] = {}
        for a in event.activities.all():
            events_count = ActivityEvent.objects.filter(activity=a).count()

            if a.matches.exists():
                context['activity_action'][a.id] = 'Архивирай дейността'
            elif events_count > 1:
                context['activity_action'][a.id] = 'Премахни дейността'
            else:
                context['activity_action'][a.id] = 'Изтрий дейността'

        return context


class AllTeamRequests(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = TeamPermissionRequest
    template_name = 'all_team_requests.html'

    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        context['pending_req'] = TeamPermissionRequest.objects\
            .select_related('team', 'team_match', 'student')\
            .filter(status='pending')\
            .order_by('submitted_at')
        context['approved_req'] = TeamPermissionRequest.objects\
            .select_related('team', 'team_match', 'student')\
            .filter(status='approved')\
            .order_by('submitted_at')[:5]
        context['rejected_req'] = TeamPermissionRequest.objects\
            .select_related('team', 'team_match', 'student')\
            .filter(status='rejected')\
            .order_by('submitted_at')[:5]

        return context


class RequestJoinTeam(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'student'

    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        profile = request.user.profile
        match_id = request.POST.get('match_id')
        event_id = request.POST.get('event_id')
        event = get_object_or_404(Event, pk=event_id)
        match = get_object_or_404(Match, pk=match_id)
        team_match = get_object_or_404(TeamMatch, match=match, team=team)

        if not profile.is_active:
            messages.error(request, 'Не си активен профил.')
            return redirect('match details', event_id=event_id, pk=match_id)

        if profile.is_banned_from_participation:
            messages.error(request, 'Ти имаш забрана за участие. Моля свържи се с учител.')
            return redirect('student dashboard')

        if team.grades.exists() and profile.grade not in team.grades.all():
            messages.error(request, 'Не си от този клас.')
            return redirect('match details', event_id=event_id, pk=match_id)

        if match.result:
            messages.error(request, 'Този мач вече е приключил.')
            return redirect('match details', event_id=event_id, pk=match_id)

        if team_match.status != 'editing':
            messages.error(request, 'Този отбор е заключен и вече не приема заявки.')
            return redirect('match details', event_id=event_id, pk=match_id)

        if team_match.students.count() >= team.number_of_players:
            messages.error(request, 'Този отбор е вече пълен и беше заключен.')
            return redirect('match details', event_id=event_id, pk=match_id)

        if not team_match.can_student_request(profile):
            messages.error(request, 'Ти вече си в отбор за този мач.')
            return redirect('match details', event_id=event_id, pk=match.pk)

        TeamPermissionRequest.objects.get_or_create(team=team, team_match=team_match, student=profile, event=event)
        return redirect('match details', event_id=event_id, pk=match_id)


class CancelTeamRequest(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'student'

    def post(self, request, pk):
        profile = request.user.profile
        team = get_object_or_404(Team, pk=pk)
        match_id = request.POST.get('match_id')
        event_id = request.POST.get('event_id')

        match = get_object_or_404(Match, pk=match_id)
        team_match = get_object_or_404(TeamMatch, match=match, team=team)

        if not profile.is_active:
            messages.error(request, 'Не си активен профил.')
            return redirect('match details', event_id=event_id, pk=match_id)

        deleted, _ = TeamPermissionRequest.objects.filter(
            team=team, team_match=team_match, student=profile, status='pending'
        ).delete()

        if deleted:
            messages.success(request, 'Зачката бе отхвърлена')
        else:
            messages.info(request, 'Няма чакащи заявки за отхвърляне.')

        return redirect('match details', event_id=event_id, pk=match_id)


class ApproveTeamRequest(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, request_id):
        req = get_object_or_404(TeamPermissionRequest, pk=request_id)

        if req.team_match.status != 'editing':
            messages.error(request, 'Този отбор е заключен и веще не приема заявки.')
            return redirect('all team requests')

        if req.team_match.students.count() >= req.team.number_of_players:
            req.team_match.status = 'locked'
            req.team_match.save(update_fields=['status'])
            messages.error(request, 'Този отбор е вече пълен и беше заключен.')
            return redirect('all team requests')

        req.status = 'approved'
        req.save(update_fields=['status'])

        TeamMatchProfile.objects.get_or_create(profile=req.student, team_match=req.team_match)
        messages.success(request, 'Успешно одобрена заявка за участие.')
        return redirect('all team requests')


class RejectTeamRequest(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, request_id):
        req = get_object_or_404(TeamPermissionRequest, pk=request_id)

        if req.team_match.status != 'editing':
            messages.error(request, 'Този отбор е заключен и веще не приема заявки.')
            return redirect('all team requests')

        if req.status == 'approved':
            TeamMatchProfile.objects.filter(
                team_match=req.team_match,
                profile=req.student
            ).delete()

        req.status = 'rejected'
        req.save(update_fields=['status'])

        messages.success(request, 'Успешно отхвърлена заявка за участие.')
        return redirect('all team requests')


class LockTeam(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        match_id = request.POST.get('match_id')
        event_id = request.POST.get('event_id')
        match = get_object_or_404(Match, pk=match_id)

        team_match = get_object_or_404(TeamMatch, team=team, match=match)
        team_match.status = 'locked'
        team_match.save(update_fields=['status'])

        return redirect('match details', event_id=event_id, pk=match_id)


class UnlockTeam(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        match_id = request.POST.get('match_id')
        event_id = request.POST.get('event_id')
        match = get_object_or_404(Match, pk=match_id)

        team_match = get_object_or_404(TeamMatch, team=team, match=match)
        team_match.status = 'editing'
        team_match.save(update_fields=['status'])

        return redirect('match details', event_id=event_id, pk=match_id)


class LeaveTeam(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'student'

    def post(self, request, pk):
        profile = request.user.profile
        team = get_object_or_404(Team, pk=pk)
        match_id = request.POST.get('match_id')
        event_id = request.POST.get('event_id')
        team_match = get_object_or_404(TeamMatch, match_id=match_id, team=team)

        if not profile.is_active:
            messages.error(request, 'Профилът не е активен.')
            return redirect('match details', event_id=event_id, pk=match_id)

        TeamMatchProfile.objects.filter(team_match=team_match, profile=profile).delete()
        TeamPermissionRequest.objects.filter(team=team, team_match=team_match, student=profile).delete()

        if match_id:
            return redirect('match details', event_id=event_id, pk=match_id)

        return redirect('student dashboard')


class AddAbsence(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == 'teacher'

    def post(self, request, profile_id):
        student = get_object_or_404(Profile, pk=profile_id)

        if not student.is_active:
            messages.error(request, 'Профилът не е активен.')
            return redirect('teacher dashboard')

        student.add_absence()

        #if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        #    return JsonResponse({'success': True, 'message': 'Отсъствието е добавено.'})

        #messages.success(request, 'Отсъствието е добавено.')
        return redirect(request.META.get('HTTP_REFERER', 'teacher_dashboard'))


class ResetAbsenceBan(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == "teacher"

    def post(self, request, profile_id):
        student = get_object_or_404(Profile, pk=profile_id)

        if not student.is_active:
            messages.error(request, 'Профилът не е активен.')
            return redirect('teacher dashboard')

        student.reset_absence_ban()
        return redirect(request.META.get('HTTP_REFERER', 'teacher_dashboard'))


class Calendar(LoginRequiredMixin, TemplateView):
    template_name = 'calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['can_edit'] = self.request.user.profile.role == 'teacher'


@login_required
@require_GET
def calendar_events(request):
    date = request.GET.get('start')

    qs = Event.objects.all()

    date_dt = date if date else None
    if date_dt:
        qs = qs.filter(date__gt=date_dt)

    data = []
    for e in qs:
        data.append({
            'id': e.id,
            'title': str(e),
            'start': e.date,
        })

    return JsonResponse(data, safe=False)


@login_required
@require_POST
def move_calendar_event(request, pk):
    if request.user.profile.role != 'teacher':
        raise PermissionDenied

    e = get_object_or_404(Event, pk=pk)

    payload = json.loads(request.body.decode('utf-8'))
    date = payload.get('start')

    if not date:
        return JsonResponse({'ok': False, 'error': 'Missing start'}, status=400)

    e.date = date
    e.save(update_fields=['date'])

    return JsonResponse({'ok': True})


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_403(request, exception):
    return render(request, '403.html', status=403)
