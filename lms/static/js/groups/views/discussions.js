(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone', 'gettext',
        'js/groups/views/divided_discussions_inline', 'js/groups/views/divided_discussions_course_wide',
        'edx-ui-toolkit/js/utils/html-utils',
        'string_utils'],

        function($, _, Backbone, gettext, InlineDiscussionsView, CourseWideDiscussionsView, HtmlUtils) {
            var hiddenClass = 'is-hidden';

            var DiscussionsView = Backbone.View.extend({
                events: {
                    'change .division-scheme': 'divisionSchemeChanged'
                },

                initialize: function(options) {
                    this.template = HtmlUtils.template($('#discussions-tpl').text());
                    this.context = options.context;
                    this.discussionSettings = options.discussionSettings;
                },

                render: function() {
                    HtmlUtils.setHtml(this.$el, this.template({availableSchemes: this.getDivisionSchemeData()}));
                    this.divisionSchemeChanged();
                    this.showDiscussionTopics();
                    return this;
                },

                getDivisionSchemeData: function() {
                    // TODO: get available schemes and currently selected scheme from this.discussionSettings
                    return [
                        {
                            key: 'none',
                            displayName: gettext('None'),
                            descriptiveText: gettext('All discussions are unified'),
                            selected: false
                        },
                        {
                            key: 'enrollment_track',
                            displayName: gettext('Enrollment Track'),
                            descriptiveText: gettext('Divide selected discussions by enrollment track'),
                            selected: false
                        },
                        {
                            key: 'cohort',
                            displayName: gettext('Cohort'),
                            descriptiveText: gettext('Divide selected discussions by cohort'),
                            selected: true
                        }

                    ];
                },

                divisionSchemeChanged: function() {
                    var selectedScheme = this.$('input[name="division-scheme"]:checked').val(),
                        topicNav = this.$('.topic-division-nav');

                    if (selectedScheme === 'none') {
                        topicNav.addClass(hiddenClass);
                    } else {
                        topicNav.removeClass(hiddenClass);
                    }
                },

                getSectionCss: function(section) {
                    return ".instructor-nav .nav-item [data-section='" + section + "']";
                },

                showDiscussionTopics: function() {
                    var dividedDiscussionsElement = this.$('.discussions-nav');
                    if (!this.CourseWideDiscussionsView) {
                        this.CourseWideDiscussionsView = new CourseWideDiscussionsView({
                            el: dividedDiscussionsElement,
                            model: this.context.discussionTopicsSettingsModel,
                            discussionSettings: this.discussionSettings
                        }).render();
                    }

                    if (!this.InlineDiscussionsView) {
                        this.InlineDiscussionsView = new InlineDiscussionsView({
                            el: dividedDiscussionsElement,
                            model: this.context.discussionTopicsSettingsModel,
                            discussionSettings: this.discussionSettings
                        }).render();
                    }
                }
            });
            return DiscussionsView;
        });
}).call(this, define || RequireJS.define);
