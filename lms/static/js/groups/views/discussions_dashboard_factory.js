(function(define, undefined) {
    'use strict';
    define(['jquery', 'js/groups/views/discussions', 'js/groups/models/cohort_discussions',
            'js/groups/models/course_discussions_settings'],
        function($, DiscussionsView, DiscussionTopicsSettingsModel, CourseDiscussionsSettingsModel) {
            return function() {
                var courseDiscussionSettings = new CourseDiscussionsSettingsModel();
                var discussionTopicsSettings = new DiscussionTopicsSettingsModel();

                var discussionsManagementElement = $('.discussions-management');

                courseDiscussionSettings.url = discussionsManagementElement.data('course-discussion-settings-url');
                discussionTopicsSettings.url = discussionsManagementElement.data('discussion-topics-url');

                var discussionsView = new DiscussionsView({
                    el: discussionsManagementElement,
                    discussionSettings: courseDiscussionSettings,
                    context: {
                        discussionTopicsSettingsModel: discussionTopicsSettings,
                        isCcxEnabled: discussionsManagementElement.data('is_ccx_enabled')
                    }
                });

                courseDiscussionSettings.fetch().done(function() {
                    discussionTopicsSettings.fetch().done(function() {
                        discussionsView.render();
                    });
                });

            };
        });
}).call(this, define || RequireJS.define);

