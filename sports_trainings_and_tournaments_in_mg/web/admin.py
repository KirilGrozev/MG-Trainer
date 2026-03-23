from django.contrib import admin
from .models import (
    Profile,
    Grade,
    Event,
    Activity,
    Match,
    Team,
    TeamMatch,
    Achievement,
    TeamPermissionRequest,
    Notification,
    Category, TeamMatchProfile,
)


class GradeInline(admin.StackedInline):
    model = Grade
    extra = 0
    can_delete = False


class TeamMatchProfileInline(admin.TabularInline):
    model = TeamMatchProfile
    extra = 0
    autocomplete_fields = ['team_match']


class TeamMatchInline(admin.TabularInline):
    model = TeamMatch
    extra = 0
    autocomplete_fields = ['team', 'match']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'is_active',
        'absence_count',
    )
    list_filter = ('role', 'is_active')
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    autocomplete_fields = ['user']
    inlines = [GradeInline, TeamMatchProfileInline]


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('profile', 'grade', 'class_letter')
    list_filter = ('grade', 'class_letter')
    search_fields = (
        'profile__user__username',
        'profile__user__email',
    )
    autocomplete_fields = ['profile']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category',)
    list_filter = ('category',)
    search_fields = ('category',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'is_active')
    list_filter = ('is_active', 'date')
    search_fields = ('name',)
    filter_horizontal = ('activities', 'achievements', 'students')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'category__category')
    filter_horizontal = ('events',)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'activity',
        'start_time',
        'duration',
        'is_active',
        'has_result',
    )
    list_filter = ('is_active', 'activity__category')
    search_fields = ('activity__name', 'activity__category__category')
    autocomplete_fields = ['activity']
    readonly_fields = ('result',)
    inlines = [TeamMatchInline]

    def has_result(self, obj):
        return bool(obj.result)
    has_result.boolean = True
    has_result.short_description = 'Result'


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'number_of_players',
        'is_active',
    )
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'category__category')


@admin.register(TeamMatch)
class TeamMatchAdmin(admin.ModelAdmin):
    list_display = ('team', 'match', 'status')
    list_filter = ('status', 'match__activity__category')
    search_fields = (
        'team__name',
        'match__activity__name',
    )
    autocomplete_fields = ['team', 'match']


@admin.register(TeamMatchProfile)
class TeamMatchProfileAdmin(admin.ModelAdmin):
    list_display = ('team_match', 'profile')
    search_fields = (
        'team_match__name',
        'profile__user__username',
        'profile__user__email',
    )
    autocomplete_fields = ['team_match', 'profile']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('events', 'teams')


@admin.register(TeamPermissionRequest)
class TeamPermissionRequestAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'team',
        'status',
        'event',
        'submitted_at',
    )
    list_filter = ('status', 'event')
    search_fields = (
        'student__user__username',
        'student__user__email',
        'team__name',
        'event__name',
    )
    autocomplete_fields = ['student', 'team', 'event']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'profile',
        'title',
        'is_read',
        'created_at',
        'event',
    )
    list_filter = ('is_read', 'created_at')
    search_fields = (
        'profile__user__username',
        'profile__user__email',
        'title',
        'message',
    )
    autocomplete_fields = ['profile', 'event']


admin.site.site_header = 'School Sports Administration'
admin.site.site_title = 'School Sports Admin'
admin.site.index_title = 'Management'
