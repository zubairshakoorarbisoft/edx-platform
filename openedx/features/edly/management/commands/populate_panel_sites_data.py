"""
Edly's management command to populate dummy data for provided sites on given date.
"""
from datetime import datetime, timedelta
import logging
from random import randint, sample, choice

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError

from edly_panel_app.api.v1.constants import REGISTRATION_FIELDS_VALUES  # pylint: disable=no-name-in-module
from edly_panel_app.api.v1.helpers import _register_user  # pylint: disable=no-name-in-module
from edly_panel_app.models import EdlyUserActivity
from figures.models import SiteDailyMetrics, SiteMonthlyMetrics, CourseDailyMetrics
from figures.sites import get_courses_for_site

from openedx.features.edly.models import EdlyMultiSiteAccess
from lms.djangoapps.grades.models import PersistentCourseGrade
from openedx.core.djangoapps.django_comment_common.models import assign_default_role
from openedx.core.djangoapps.django_comment_common.utils import seed_permissions_roles
from student.helpers import AccountValidationError
from student.roles import CourseInstructorRole, CourseStaffRole
from student import auth
from student.models import CourseAccessRole, CourseEnrollment
from util.organizations_helpers import add_organization_course, get_organization_by_short_name
from xmodule.course_module import CourseFields
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import DuplicateCourseError

logger = logging.getLogger(__name__)

first_names = [
    'john', 'emily', 'michael', 'sarah', 'david', 'lisa', 'james', 'emma', 'robert', 'olivia', 
    'william', 'sophia', 'joseph', 'ava', 'daniel', 'isabella', 'matthew', 'mia', 'andrew', 
    'charlotte', 'christopher', 'amelia', 'joshua', 'harper', 'ryan', 'evelyn', 'ethan', 'abigail', 
    'tyler', 'madison', 'brandon', 'ella', 'nicholas', 'grace', 'nathan', 'chloe', 'logan', 'zoey', 
    'gabriel', 'lily', 'justin', 'hannah', 'lucas', 'addison', 'jack', 'riley', 'aaron', 'layla', 
    'christian', 'elena', 'sam', 'aubrey', 'connor', 'stella', 'hunter', 'aurora', 'ian', 'penelope', 
    'carter', 'skylar', 'jordan', 'elena', 'mason', 'nova', 'luke', 'zoe', 'dylan', 'scarlett', 'cameron', 
    'aria', 'xavier', 'madison', 'isaac', 'brooklyn', 'adam', 'claire', 'jason', 'nora', 'owen', 'lucy', 
    'julian', 'aurora', 'leo', 'savannah', 'miles', 'hazel', 'oscar', 'violet', 'ezra', 'aurora', 'jose', 
    'stella', 'calvin', 'luna', 'roman'
]

last_names = [
    'smith', 'jones', 'brown', 'davis', 'wilson', 'taylor', 'anderson', 'thomas', 'jackson', 
    'white', 'harris', 'martin', 'thompson', 'garcia', 'martinez', 'robinson', 'clark', 'rodriguez', 
    'lewis', 'lee', 'walker', 'hall', 'allen', 'young', 'hernandez', 'king', 'wright', 'lopez', 
    'hill', 'scott', 'green', 'adams', 'baker', 'gonzalez', 'nelson', 'carter', 'mitchell', 'perez', 
    'roberts', 'turner', 'phillips', 'campbell', 'parker', 'evans', 'edwards', 'collins', 'stewart', 
    'sanchez', 'morris', 'rogers', 'reed', 'cook', 'morgan', 'bell', 'murphy', 'bailey', 'rivera', 
    'cooper', 'richardson', 'cox', 'howard', 'ward', 'torres', 'peterson', 'gray', 'ramirez', 'james', 
    'watson', 'brooks', 'kelly', 'sanders', 'price', 'bennett', 'wood', 'barnes', 'ross', 'henderson', 
    'coleman', 'jenkins', 'perry', 'powell', 'long', 'patterson', 'hughes', 'flores', 'washington', 
    'butler', 'simmons', 'foster', 'gonzales', 'bryant', 'alexander', 'russell', 'griffin', 'diaz'
]


class Command(BaseCommand):
    """
    Populate dummy data for given sites for provided date.
    """
    help = 'Populate panel sites data in edly insights for given list of sites.'

    def add_arguments(self, parser):
        """
        Add arguments for email list and date for reports.
        """
        parser.add_argument(
            '--sites',
            default='',
            help='Comma separated list of lms sites',
        )
        parser.add_argument(
            '--date',
            default=datetime.today().strftime('%m/%Y'),
            help='The month and year of the data to populate.'
        )
    
    def get_site_user_count(self, sub_org):
        """return the number of user for a given site."""
        return EdlyMultiSiteAccess.objects.filter(sub_org=sub_org).count()

    def get_dummy_users(self):
        """
        Return random number of dummy users to register.
        """
        dummy_users = []
        users_count = randint(50, 70)
        password = 'edx@123.aA'
        REGISTRATION_FIELDS_VALUES.pop('username')
        REGISTRATION_FIELDS_VALUES.pop('name')
        REGISTRATION_FIELDS_VALUES.pop('password')
        REGISTRATION_FIELDS_VALUES.pop('email')
        REGISTRATION_FIELDS_VALUES.pop('confirm_email')
        for index in range(1, users_count):
            username = '{}_{}'.format(choice(first_names), choice(last_names))
            dummy_users.append(dict(
                username='{}'.format(username),
                email='{}@example.com'.format(username),
                name='{}'.format(username),
                password=password,
                **REGISTRATION_FIELDS_VALUES,
            ))

        return dummy_users

    def get_dummy_courses(self, organization, populate_date):
        """
        Return random number of dummy courses to create.
        """
        course_name_prefix = [
            'Test Demo Course', 'Demo Course with Edly SaaS', 'Intro to Demo Course', 'Demo Course for Beginners',
            'Advanced Demo Course', 'Complete Guide to Demo Course', 'Demo Course: Getting Started', 
            'Exploring Demo Course Features', 'Mastering Demo Course Techniques', 'Demo Course: From Beginner to Pro',
            'Demo Course for SaaS Enthusiasts', 'Next-Level Demo Course', 'Demo Course: A Comprehensive Overview',
            'Demo Course for Edly Users', 'Hands-on Demo Course', 'Live Demo Course', 'Demo Course for Educational Platforms',
            'Learn with Demo Course', 'Interactive Demo Course', 'Practical Demo Course'
        ]
        course_count = randint(5, 8)
        courses = []
        month_for = populate_date.month
        year_for = populate_date.year
        for course in range(1, course_count):
            course_name = ('{} {} {}/{}').format(
                course_name_prefix[randint(0,19)],
                course, month_for,
                year_for
            )
            course_number = ('DC_{}_{}{}').format(course_count, month_for, year_for)
            course_run = '{}_{}'.format(month_for, year_for)
            courses.append(
                dict(
                    display_name=course_name,
                    number=course_number,
                    run=course_run,
                    org=organization,
                )
            )

        return courses

    def initialize_permissions(self, course_key, user_who_created_course):
        """
        Initializes a new course by enrolling the course creator as a student,
        and initializing Forum by seeding its permissions and assigning default roles.
        """
        seed_permissions_roles(course_key)
        CourseEnrollment.enroll(user_who_created_course, course_key)
        assign_default_role(course_key, user_who_created_course)

    def add_instructor(self, course_key, requesting_user, new_instructor):
        """
        Adds given user as instructor and staff to the given course,
        after verifying that the requesting_user has permission to do so.
        """
        CourseInstructorRole(course_key).add_users(new_instructor)
        auth.add_users(requesting_user, CourseStaffRole(course_key), new_instructor)

    def create_new_course_in_store(self, store, user, org, number, run, fields):
        """
        Creates the new course in module store.
        """
        fields.update({
            'language': getattr(settings, 'DEFAULT_COURSE_LANGUAGE', 'en'),
            'cert_html_view_enabled': True,
            'start': datetime(2023, 1, 1),
        })

        with modulestore().default_store(store):
            new_course = modulestore().create_course(
                org,
                number,
                run,
                user.id,
                fields=fields,
            )
        
        try: 
            self.add_instructor(new_course.id, user, user)
            self.initialize_permissions(new_course.id, user)
        except Exception as err:
            logger.exception('Unable to add course instructor/permission: {}'.format(str(err)))

        return new_course

    def create_new_course(self, user, org, number, run, fields):
        """
        Create a new course run.

        Raises:
            DuplicateCourseError: Course run already exists.
        """
        store_for_new_course = modulestore().default_modulestore.get_modulestore_type()
        new_course = self.create_new_course_in_store(store_for_new_course, user, org, number, run, fields)
        org_data = get_organization_by_short_name(org)
        add_organization_course(org_data, new_course.id)
        return new_course

    def get_dummy_metrics(self, date):
        """
        Returns random dates within month with dummy data.
        """
        start_date = date
        end_date = date + timedelta(days=30)
        number_of_dates = 15
        dummy_dates = [start_date]

        while start_date != end_date:
            start_date += timedelta(days=1)
            dummy_dates.append(start_date)

        dates = []
        dummy_dates = sample(dummy_dates, number_of_dates)
        dummy_dates.append(start_date)
        for _date in dummy_dates:
            dates.append(dict(
                date_for=_date,
                todays_active_user_count=randint(10, 30),
                todays_active_learners_count=randint(10, 30),
                total_user_count=randint(10, 30),
                course_count=randint(10, 30),
                total_enrollment_count=randint(10, 30),
            ))

        return dates

    def register_dummy_users(self, site, dummy_users):
        """
        Registers dummy users for provided site.
        """
        extra_fields = site.configuration.get_value(
                'DJANGO_SETTINGS_OVERRIDE', {}
        ).get('REGISTRATION_EXTRA_FIELDS', {})

        for user in dummy_users:
            try:
                logger.info('Registering user: {}'.format(user['username']))
                _register_user(
                    params=user,
                    site=site,
                    site_configuration=dict(extra_fields=extra_fields),
                    message_context={},
                    tos_required=False,
                    skip_email=True,
                )
            except (AccountValidationError, ValidationError) as err:
                logger.info('Failure registering user: {}'.format(user['username']))
                logger.info('Failure in user registration: {}'.format(err))
                pass
            except Exception as err:
                logger.exception('Failure registering user: {}'.format(user['username']))
                pass

    def create_dummy_courses(self, edx_org, courses):
        """
        Creates dummy courses in module store for given edx organization.
        """
        course_access_role = CourseAccessRole.objects.filter(org=edx_org, role= 'global_course_creator')
        if not course_access_role.exists():
            return []

        user = course_access_role.first().user
        new_courses = []
        for course in courses:
            try:
                logger.info('Creating Dummy Course: {}'.format(course['run']))
                new_course = self.create_new_course(
                    user=user,
                    org=edx_org,
                    number=course.get('number'),
                    run=course.get('run'),
                    fields=dict(
                        display_name=course.get('display_name'),
                        wiki_slug=u"{0}.{1}.{2}".format(edx_org, course.get('number'), course.get('run'),),
                        start=CourseFields.start.default,
                    )
                )
                new_courses.append(new_course)
            except DuplicateCourseError:
                pass
            except Exception as err:
                pass

        return new_courses

    def add_dummy_edly_activities(self, users, edly_sub_orgs, date):
        """
        Add users to edly sub organization and creates user activities.
        """
        for user in users:
            logger.info('Saving edly user activity')
            for edly_sub_org in edly_sub_orgs:
                edly_access_user, _ = EdlyMultiSiteAccess.objects.get_or_create(user=user, sub_org=edly_sub_org)
                try:
                    EdlyUserActivity.objects.get_or_create(
                        user=edly_access_user.user,
                        activity_date=date,
                        edly_sub_organization=edly_sub_org,
                    )
                except Exception:  # pylint: disable=broad-except
                    logger.exception('Unable to add edly_user_activity')

    def create_course_daily_matric(self, courses, sites, dates):
        """Generate courses daily matrix."""
        for site in sites: 
            today = datetime.today()
            course_id = get_courses_for_site(site)
            random_courses = sample(list(course_id), min(len(course_id), 20))
            courses = [{'id': id} for id in random_courses]

            for course_id in courses:
                try:
                    rec = dict(
                        site=site
                    )
                    rec['date_for'] = today
                    rec['enrollment_count'] = randint(10,50)
                    rec['active_learners_today'] = randint(10,50)
                    rec['active_learners_this_month'] = randint(10,50)
                    rec['average_progress'] = round(randint(1,100)/100, 2)
                    rec['average_days_to_complete'] = randint(1,30)
                    rec['num_learners_completed'] = randint(10,50)
                    sdm, _ = CourseDailyMetrics.objects.get_or_create(
                        date_for=rec['date_for'],
                        site_id=rec['site'].id,
                        course_id = str(course_id['id']),
                        defaults=rec,
                    )
                    sdm.save()
                except Exception as err:
                    logger.info('Error populating Course Daily Metrics: {}'.format(err))

    def enroll_dummy_users_in_courses(self, courses, users, site):
        """
        Enrolls users in courses.
        """
        if not len(courses):
            course_id = get_courses_for_site(site)
            courses = [{'id': id} for id in course_id[:8]]
        
        if not len(users):
            edly_sub_org = getattr(site, 'edly_sub_org_for_lms', None)
            user_ids = EdlyMultiSiteAccess.objects.filter(
                sub_org=edly_sub_org, groups__name=settings.EDLY_PANEL_RESTRICTED_USERS_GROUP
            ).values_list('user', flat=True)
            users = get_user_model().objects.filter(id__in=user_ids)

        num_to_sample = min(len(users), 10)
        users = sample(list(users), num_to_sample)
        for course in courses:
            for user in users:
                try:
                    course_id = getattr(course, 'id') if getattr(course, 'id', None) else str(course['id'])
                    logger.info('Enrolling user {} in course {}'.format(user.username, course_id))
                    CourseEnrollment.enroll(user, course_id)
                    percent_grade  = randint(50, 100)
                    self.params = {
                        'user_id': user.id,
                        'course_id': getattr(course, 'id'),
                        'percent_grade': percent_grade,
                        'passed': True if percent_grade > 50 else False
                    }
                    grade = PersistentCourseGrade.update_or_create(**self.params)
                    grade.passed_timestamp = datetime.strptime(datetime.today(), '%d-%m-%Y').date()
                    grade.save()
                except Exception as err:
                    logger.info('Enrolling user failed with Error: {}'.format(err))


    def create_staff_users(self, org, users):
        staff_users_count = CourseAccessRole.objects.filter(
            org=org
        ).count()
        
        if staff_users_count > 50: 
            return 

        to_pick = 5
        if len(users) < to_pick:
            to_pick = len(users)

        indices = list(range(len(users)))
        indices = sample(indices, to_pick)
        for index in indices:
            CourseAccessRole.objects.get_or_create(
                user=users[index],
                org=org,
                role='global_course_creator',
            )

    def handle(self, *args, **options):
        """
        Command to populate panel site data for provided sites and date.
        """
        logger.info('Populating sites data.')
        sites_list = options['sites'].split(',')
        date_string = options['date']
        try:
            populate_date = datetime.strptime(date_string, '%m/%Y')
        except ValueError:
            raise CommandError(
                'The provided input date {} format is invalid. Please provide date in the format mm/yyyy'.format(
                    date_string,
                )
            )

        sites = list(Site.objects.filter(domain__in=sites_list))
        dates = self.get_dummy_metrics(populate_date)
        dummy_users = self.get_dummy_users()

        edly_sub_orgs = []
        for site in sites:
            edly_sub_org = getattr(site, 'edly_sub_org_for_lms', None)
            if not edly_sub_org:
                continue

            logger.info('Starting adding data for site: {}'.format(site))
            edly_sub_orgs.append(edly_sub_org)
            if self.get_site_user_count(edly_sub_org) < 220:
                self.register_dummy_users(site, dummy_users)

            logger.info('Saving Site Monthly Metrics')
            smm, _ = SiteMonthlyMetrics.objects.get_or_create(
                month_for=populate_date,
                site=site,
                defaults=dict(active_user_count=randint(10, 30)),
            )
            smm.save()

            for date in dates:
                logger.info('Saving Site Daily Metrics')
                sdm, _ = SiteDailyMetrics.objects.get_or_create(
                    date_for=date['date_for'],
                    site_id=site.id,
                    defaults=date,
                )
                sdm.save()

        edx_organizations = []
        for edly_sub_org in edly_sub_orgs:
            edx_organizations.extend([edly_sub_org.edx_organizations.all().first().short_name])

        user_objects = get_user_model().objects.filter(username__in=[user['username']for user in dummy_users])
        logger.info('Adding dummy user activities')
        self.add_dummy_edly_activities(user_objects, edly_sub_orgs, populate_date)

        new_courses = []
        for edx_org,site in zip(edx_organizations, sites):
            if len(get_courses_for_site(site)) < 25: 
                courses = self.get_dummy_courses(edx_org, populate_date)
                new_courses.extend(self.create_dummy_courses(edx_org, courses))

        for site in sites:
            self.create_course_daily_matric(courses, sites, dates)
            self.enroll_dummy_users_in_courses(new_courses, user_objects, site)

        for edx_org in edx_organizations:
            self.create_staff_users(edx_org, user_objects)

        logger.info('All sites data has been populated.')
