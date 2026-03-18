from django.urls import path

from sports_trainings_and_tournaments_in_mg.web.views import Home, StudentDashboard, TeacherDashboard, \
    CreateAchievement, CreateEvent, EditEvent, EventDetails, Calendar, AdditionalStudentInfo, CreateActivity, \
    DashboardRedirect, EditStudentCategories, ActivityDetails, MatchDetails, CreateMatch, \
    CreateTeam, MatchResultView, RequestJoinTeam, ApproveTeamRequest, LockTeam, \
    RejectTeamRequest, AllTeamRequests, EditActivity, AddExistingTeam, LeaveTeam, CancelTeamRequest, \
    AddEventAchievement, AddTeamAchievement, calendar_events, move_calendar_event, AddAbsence, ResetAbsenceBan, \
    student_email_suggestions, RemoveTeam, ArchiveTeam, EditMatch, ArchiveMatch, ArchiveEvent, ArchiveActivity, \
    UnlockTeam

urlpatterns = [
    path('', Home.as_view(), name='home'),
    #path('accounts/login/', GoogleLoginRedirectView.as_view(), name='account login'),
    path('dashboard-redirect/', DashboardRedirect.as_view(), name='dashboard redirect'),
    path('student/additional-info/', AdditionalStudentInfo.as_view(), name='additional info'),
    path('student/edit/categories/', EditStudentCategories.as_view(), name='edit student categories'),
    path('student/dashboard/', StudentDashboard.as_view(), name='student dashboard'),
    path('teacher/dashboard/', TeacherDashboard.as_view(), name='teacher dashboard'),
    path('teacher/students/suggestions/', student_email_suggestions, name='student email suggestions'),
    path('teacher/requests/', AllTeamRequests.as_view(), name='all team requests'),
    path('teacher/create/achievement/', CreateAchievement.as_view(), name='create achievement'),
    path('teacher/event/<int:pk>/achievement/add/', AddEventAchievement.as_view(), name='add event achievement'),
    path('teacher/team/<int:pk>/achievements/add/', AddTeamAchievement.as_view(), name='add team achievements'),
    path('teacher/<int:activity_id>/create/match/', CreateMatch.as_view(), name='create match'),
    path('teacher/edit/match/<int:pk>/', EditMatch.as_view(), name='edit match'),
    path('teacher/archive/match/<int:pk>/', ArchiveMatch.as_view(), name='archive match'),
    path('events/<int:event_id>/match-details/<int:pk>/', MatchDetails.as_view(), name='match details'),
    path('match-result/<int:pk>/', MatchResultView.as_view(), name='match result'),
    path('teacher/<int:event_id>/create/activity/', CreateActivity.as_view(), name='create activity'),
    path('teacher/edit/activity/<int:id>/', EditActivity.as_view(), name='edit activity'),
    path('teacher/archive/activity/<int:pk>/', ArchiveActivity.as_view(), name='archive activity'),
    path('events/<int:event_id>/activity-details/<int:pk>/', ActivityDetails.as_view(), name='activity details'),
    path('teacher/<int:match_id>/create/team/', CreateTeam.as_view(), name='create team'),
    path('teacher/match/<int:pk>/team/add', AddExistingTeam.as_view(), name='add existing team'),
    path('teacher/remove/team/<int:pk>/', RemoveTeam.as_view(), name='remove team'),
    path('student/leave/team/<int:pk>/', LeaveTeam.as_view(), name='leave team'),
    path('teacher/archive/team/<int:pk>/', ArchiveTeam.as_view(), name='archive team'),
    path('teacher/create/achievement/', CreateAchievement.as_view(), name='create achievement'),
    path('teacher/create/event/', CreateEvent.as_view(), name='create event'),
    path('teacher/edit/event/<int:pk>/', EditEvent.as_view(), name='edit event'),
    path('teacher/archive/event/<int:pk>/', ArchiveEvent.as_view(), name='archive event'),
    path('event-details/<int:pk>/', EventDetails.as_view(), name='event details'),
    path('request-join-team/<int:pk>/', RequestJoinTeam.as_view(), name='request join team'),
    path('cancel-team-request/<int:pk>/', CancelTeamRequest.as_view(), name='cancel team request'),
    path('approve-team-request/<int:request_id>/', ApproveTeamRequest.as_view(), name='approve team request'),
    path('reject-team-request/<int:request_id>/', RejectTeamRequest.as_view(), name='reject team request'),
    path('lock-team/<int:pk>/', LockTeam.as_view(), name='lock team'),
    path('unlock-team/<int:pk>/', UnlockTeam.as_view(), name='unlock team'),
    path('students/<int:profile_id>/absence/add/', AddAbsence.as_view(), name='add absence'),
    path('students/<int:profile_id>/absence/reset/', ResetAbsenceBan.as_view(), name='reset absence ban'),
    path('calendar/', Calendar.as_view(), name='calendar'),
    path('api/calendar/events/', calendar_events, name='calendar events'),
    path('api/calendar/events/<int:pk>/move/', move_calendar_event, name='move calendar event')
]

handler404 = 'sports_trainings_and_tournaments_in_mg.web.views.custom_404'
