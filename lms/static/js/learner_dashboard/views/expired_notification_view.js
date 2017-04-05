(function(define) {
    'use strict';
    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'text!../../../templates/learner_dashboard/expired_notification.underscore',
        'text!../../../templates/learner_dashboard/certificate_icon.underscore'
    ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             expiredNotificationTpl,
             certificateIconTpl
         ) {
             return Backbone.View.extend({
                 statusTpl: HtmlUtils.template(expiredNotificationTpl),
                 iconTpl: HtmlUtils.template(certificateIconTpl),

                 initialize: function(options) {
                     this.$el = options.$el;
                     this.render();
                 },

                 render: function() {
                     var data = this.model.toJSON();

                     data = $.extend(data, {certificateSvg: this.iconTpl()});
                     HtmlUtils.setHtml(this.$el, this.statusTpl(data));
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
