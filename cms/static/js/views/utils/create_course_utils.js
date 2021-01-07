/**
 * Provides utilities for validating courses during creation, for both new courses and reruns.
 */
define(['jquery', 'gettext', 'common/js/components/utils/view_utils', 'js/views/utils/create_utils_base'],
    function($, gettext, ViewUtils, CreateUtilsFactory) {
        'use strict';
        return function(selectors, classes) {
            var keyLengthViolationMessage = gettext('The combined length of the organization, course number, ' +
              'and course run fields cannot be more than <%- limit %> characters.');
            var keyFieldSelectors = [selectors.org, selectors.number, selectors.run];
            var nonEmptyCheckFieldSelectors = [selectors.name, selectors.org, selectors.number, selectors.run];

            CreateUtilsFactory.call(this, selectors, classes, keyLengthViolationMessage, keyFieldSelectors, nonEmptyCheckFieldSelectors);

            this.setupOrgAutocomplete = function() {
                $.getJSON('/organizations', function(data) {
                    $(selectors.org).autocomplete({
                        source: data
                    });
                });
            };

            this.setUpSiteAutoComplete = function() {
                if ($(selectors.site).children().length > 1) {
                    // No need to repopulate the site dropdown if it's already populated.
                    return;
                }

                $(selectors.site).append(
                    $('<option>', {
                        value: 'Public',
                        text: 'Public'
                    })
                );


                $.getJSON('/clearesult/api/v0/sites/', function(data) {
                    $.each(data, function(i, item) {
                        $(selectors.site).append(
                            $('<option>', {
                                value: item.domain,
                                text: item.domain
                            })
                        );
                    });
                });
            };

            this.create = function(courseInfo, errorHandler) {
                $.postJSON(
                    '/course/',
                    courseInfo,
                    function(data) {
                        if (data.url !== undefined) {
                            ViewUtils.redirect(data.url);
                        } else if (data.ErrMsg !== undefined) {
                            errorHandler(data.ErrMsg);
                        }
                    }
                );
            };
        };
    });
