/* eslint-env node */

'use strict';

var path = require('path');
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');
var StringReplace = require('string-replace-webpack-plugin');

var files = require('./webpack-config/file-lists.js');

var filesWithRequireJSBlocks = [
    path.resolve(__dirname, 'common/static/common/js/components/utils/view_utils.js'),
    /descriptors\/js/,
    /modules\/js/,
    /common\/lib\/xmodule\/xmodule\/js\/src\//,
];

var defineHeader = /\(function ?\(((define|require|requirejs|\$)(, )?)+\) ?\{/;
var defineCallFooter = /\}\)\.call\(this, ((define|require)( \|\| RequireJS\.(define|require))?(, )?)+?\);/;
var defineDirectFooter = /\}\(((window\.)?(RequireJS\.)?(requirejs|define|require|jQuery)(, )?)+\)\);/;
var defineFancyFooter = /\}\).call\(\s*this(\s|.)*define(\s|.)*\);/;
var defineFooter = new RegExp('(' + defineCallFooter.source + ')|(' + defineDirectFooter.source + ')|(' + defineFancyFooter.source + ')', 'm');

module.exports = {
    context: __dirname,

    entry: {
        // Studio
        Import: './cms/static/js/features/import/factories/import.js',
        CourseOrLibraryListing: './cms/static/js/features_jsx/studio/CourseOrLibraryListing.jsx',
        'js/pages/login': './cms/static/js/pages/login.js',
        'js/pages/textbooks': './cms/static/js/pages/textbooks.js',
        'js/pages/container': './cms/static/js/pages/container.js',
        'js/sock': './cms/static/js/sock.js',

        // LMS
        SingleSupportForm: './lms/static/support/jsx/single_support_form.jsx',
        AlertStatusBar: './lms/static/js/accessible_components/StatusBarAlert.jsx',
        LearnerAnalyticsDashboard: './lms/static/js/learner_analytics_dashboard/LearnerAnalyticsDashboard.jsx',
        UpsellExperimentModal: './lms/static/common/js/components/UpsellExperimentModal.jsx',
        PortfolioExperimentUpsellModal: './lms/static/common/js/components/PortfolioExperimentUpsellModal.jsx',
        EntitlementSupportPage: './lms/djangoapps/support/static/support/jsx/entitlements/index.jsx',

        // Learner Dashboard
        EntitlementFactory: './lms/static/js/learner_dashboard/course_entitlement_factory.js',
        EntitlementUnenrollmentFactory: './lms/static/js/learner_dashboard/entitlement_unenrollment_factory.js',
        ProgramDetailsFactory: './lms/static/js/learner_dashboard/program_details_factory.js',
        ProgramListFactory: './lms/static/js/learner_dashboard/program_list_factory.js',
        UnenrollmentFactory: './lms/static/js/learner_dashboard/unenrollment_factory.js',
        ViewedEvent: './lms/static/completion/js/ViewedEvent.js',

        // Features
        CourseGoals: './openedx/features/course_experience/static/course_experience/js/CourseGoals.js',
        CourseHome: './openedx/features/course_experience/static/course_experience/js/CourseHome.js',
        CourseOutline: './openedx/features/course_experience/static/course_experience/js/CourseOutline.js',
        CourseSock: './openedx/features/course_experience/static/course_experience/js/CourseSock.js',
        CourseTalkReviews: './openedx/features/course_experience/static/course_experience/js/CourseTalkReviews.js',
        Currency: './openedx/features/course_experience/static/course_experience/js/currency.js',
        Enrollment: './openedx/features/course_experience/static/course_experience/js/Enrollment.js',
        LatestUpdate: './openedx/features/course_experience/static/course_experience/js/LatestUpdate.js',
        WelcomeMessage: './openedx/features/course_experience/static/course_experience/js/WelcomeMessage.js',

        // Common
        ReactRenderer: './common/static/js/src/ReactRenderer.jsx',

        'descriptors/js/all': [
            'descriptors/js/000-58032517f54c5c1a704a908d850cbe64',
            'descriptors/js/001-091f58dd32678373423e4deae364e9dd',
            'descriptors/js/001-6022911bfee6e7865b4457629ab2ff44',
            'descriptors/js/001-77e70463a4253744c48f1687383e259e',
            'descriptors/js/001-79a64f2010d8b4cb8d0f0d6912c70c12',
            'descriptors/js/001-bb51a36b4a29ce38be91a5102d77ad3c',
            'descriptors/js/001-bdf940d1aa93739db56b49bf7c25205e',
            'descriptors/js/001-d0d45e2d20a67233658cef6d8d2ce5ed',
        ],
        'modules/js/all': [
            'modules/js/000-58032517f54c5c1a704a908d850cbe64.js',
            'modules/js/001-3918b2d4f383c04fed8227cc9f523d6e.js',
            'modules/js/001-550e26b7e4efbc0c68a580f6dbecf66c.js',
            'modules/js/001-8fca1cf6348bb2601d363cac06d8f462.js',
            'modules/js/001-b65f0935afe77035b05378d91e6f85cd.js',
            'modules/js/001-be1d5c5125cbd663bb0bc2f0da76180a.js',
            'modules/js/001-ea4a77e358caed4d3ed14b4c083b5d84.js',
            'modules/js/002-07b34731f5211b15aee90f3a9bc9a772.js',
            'modules/js/002-4cdcf6c69f17c03a3f92c5184c057f16.js',
            'modules/js/002-68fe6acc2bb55e9e46091531c67e0c3d.js',
            'modules/js/002-7b78d6e6a55569534f7be0666a0ce61e.js',
            'modules/js/002-d47e678753905042c21bbc110fb3f8d8.js',
            'modules/js/003-0a342bc7d30f067a02c94cae22e72fec.js',
            'modules/js/003-11b555a0f42bb03a6058fb5ed94524bb.js',
            'modules/js/003-98cb8ef870a77a10f053783eba6f771d.js',
            'modules/js/003-d47e678753905042c21bbc110fb3f8d8.js',
            'modules/js/004-26caba6f71877f63a7dd4f6796109bf6.js',
            'modules/js/004-463478e0fa9cda11e791826cf2b01712.js',
            'modules/js/004-b0c34afa95eaa6b45d843d92ca523a94.js',
            'modules/js/005-d7c55ec8a30fcc491c039893a74aaa7f.js',
            'modules/js/005-bcacb1e7d24bd0406b078f3692e5ed88.js',
            'modules/js/006-b015608ae83476ba681ef2efaa5ded36.js',
            'modules/js/007-e2ba591ebbbddc42eabb7d4acd57c1b8.js',
            'modules/js/008-1d9c1f637bb37accbbae26e38c3bf4a2.js',
            'modules/js/009-179c6f60d7f5f213a7f09732c75e498a.js',
            'modules/js/010-fe66b177471a3b37691d3919dc51c451.js',
            'modules/js/011-17fca34144ea38180538f1d89eab122c.js',
            'modules/js/012-0a5ac4b114b9d9f3efd68424ba99b335.js',
            'modules/js/013-86e37ec56c93011b450d439e44fad383.js',
            'modules/js/014-c104fbf3a3e22f0c4b7bc6c93137988d.js',
            'modules/js/015-0d3079d4b0813c00939c6a58f6422fac.js',
            'modules/js/016-5ccd2a6e34e24bc65b27c9ba0c86c8a5.js',
            'modules/js/017-12ebf16a2411048ae60f9bbd3bf76864.js',
            'modules/js/018-04f6b031a15274732292ee2e2c05aab3.js',
            'modules/js/019-2d23914518eb446fa06d09d98bdc8743.js',
            'modules/js/020-3dc64e04bce527f8b8fbf01a49db6953.js',
            'modules/js/021-45dc530bf8cdf064091ed13053f2248d.js',
            'modules/js/022-ed1239609795bce92dd2dd489361f339.js',
            'modules/js/023-591cbbd90a05b3328567937e601f087d.js',
            'modules/js/024-aa30a89165618e08751680b709214b51.js',
            'modules/js/025-5af1e4e2539aecdc23ee30171765865d.js',
            'modules/js/026-4a8a9ee2a7523143652a06668f00aa49.js',
            'modules/js/027-95b8a289a700658622b24f55c1250764.js',
            'modules/js/028-0f29fb25c1053596cd8d5505c00e487c.js',
            'modules/js/029-60a6c4f5a89bbfbe68a5f8e2369d2172.js',
            'modules/js/030-cd789928aa3c5b7206028b2afc16cd13.js',
            'modules/js/031-0f4005cdd75d75f578e0c215967aaac5.js',
            'modules/js/032-076e3448a3ad7741e28f926565666245.js',
            'modules/js/033-8d60f6dee0a19ca7f9d7bbccf816b7e0.js',
            'modules/js/034-d6d8c7d542edd9cf783c08cee3ef6e44.js',
            'modules/js/035-b5c924b18e68709de546ed6a2dc577ec.js',
        ]
    },

    output: {
        path: path.resolve(__dirname, 'common/static/bundles'),
        libraryTarget: 'window'
    },

    plugins: [
        new webpack.NoEmitOnErrorsPlugin(),
        new webpack.NamedModulesPlugin(),
        new BundleTracker({
            path: process.env.STATIC_ROOT_CMS,
            filename: 'webpack-stats.json'
        }),
        new BundleTracker({
            path: process.env.STATIC_ROOT_LMS,
            filename: 'webpack-stats.json'
        }),
        new webpack.ProvidePlugin({
            _: 'underscore',
            $: 'jquery',
            jQuery: 'jquery',
            'window.jQuery': 'jquery',
            Popper: 'popper.js', // used by bootstrap
            CodeMirror: 'codemirror',
        }),

        // Note: Until karma-webpack releases v3, it doesn't play well with
        // the CommonsChunkPlugin. We have a kludge in karma.common.conf.js
        // that dynamically removes this plugin from webpack config when
        // running those tests (the details are in that file). This is a
        // recommended workaround, as this plugin is just an optimization. But
        // because of this, we really don't want to get too fancy with how we
        // invoke this plugin until we can upgrade karma-webpack.
        new webpack.optimize.CommonsChunkPlugin({
            // If the value below changes, update the render_bundle call in
            // common/djangoapps/pipeline_mako/templates/static_content.html
            name: 'commons',
            filename: 'commons.js',
            minChunks: 3
        })
    ],

    module: {
        noParse: [
            // See sinon/webpack interaction weirdness:
            // https://github.com/webpack/webpack/issues/304#issuecomment-272150177
            // (I've tried every other suggestion solution on that page, this
            // was the only one that worked.)
            /\/sinon\.js|codemirror-compressed\.js/
        ],
        rules: [
            {
                test: files.namespacedRequire.concat(files.textBangUnderscore, filesWithRequireJSBlocks),
                loader: StringReplace.replace(
                    ['babel-loader'],
                    {
                        replacements: [
                            {
                                pattern: defineHeader,
                                replacement: function() { return ''; }
                            },
                            {
                                pattern: defineFooter,
                                replacement: function() { return ''; }
                            },
                            {
                                pattern: /(\/\* RequireJS) \*\//g,
                                replacement: function (match, p1) { return p1; }
                            },
                            {
                                pattern: /\/\* Webpack/g,
                                replacement: function (match) { return match + ' */'; }
                            },
                            {
                                pattern: /text!(.*?\.underscore)/g,
                                replacement: function (match, p1) { return p1; }
                            }
                        ]
                    }
                )
            },
            {
                test: filesWithRequireJSBlocks,
                loader: StringReplace.replace(
                    ['babel-loader'],
                    {
                        replacements: [
                            {
                                pattern: /(\/\* RequireJS) \*\//g,
                                replacement: function (match, p1) { return p1; }
                            },
                            {
                                pattern: /\/\* Webpack/g,
                                replacement: function (match) { return match + ' */'; }
                            }
                        ]
                    }
                )
            },
            {
                test: /\.(js|jsx)$/,
                exclude: [
                    /node_modules/,
                    files.namespacedRequire,
                    files.textBangUnderscore,
                    filesWithRequireJSBlocks
                ],
                use: 'babel-loader'
            },
            {
                test: /\.(js|jsx)$/,
                include: [
                    /paragon/
                ],
                use: 'babel-loader'
            },
            {
                test: path.resolve(__dirname, 'common/static/coffee/src/ajax_prefix.js'),
                use: [
                    'babel-loader',
                    {
                        loader: 'exports-loader',
                        options: {
                            'this.AjaxPrefix': true
                        }
                    }
                ]
            },
            {
                test: /\.underscore$/,
                use: 'raw-loader'
            },
            {
                // This file is used by both RequireJS and Webpack and depends on window globals
                // This is a dirty hack and shouldn't be replicated for other files.
                test: path.resolve(__dirname, 'cms/static/cms/js/main.js'),
                loader: StringReplace.replace(
                    ['babel-loader'],
                    {
                        replacements: [
                            {
                                pattern: /\(function\(AjaxPrefix\) {/,
                                replacement: function() { return ''; }
                            },
                            {
                                pattern: /], function\(domReady, \$, str, Backbone, gettext, NotificationView\) {/,
                                replacement: function() {
                                    // eslint-disable-next-line
                                    return '], function(domReady, $, str, Backbone, gettext, NotificationView, AjaxPrefix) {';
                                }
                            },
                            {
                                pattern: /'..\/..\/common\/js\/components\/views\/feedback_notification',/,
                                replacement: function() {
                                    return "'../../common/js/components/views/feedback_notification', 'AjaxPrefix',";
                                }
                            },
                            {
                                pattern: /}\).call\(this, AjaxPrefix\);/,
                                replacement: function() { return ''; }
                            }
                        ]
                    }
                )
            },
            {
                test: /\.(woff2?|ttf|svg|eot)(\?v=\d+\.\d+\.\d+)?$/,
                loader: 'file-loader'
            },
            {
                test: /xblock\/core/,
                loader: 'exports-loader?this.XBlock!imports-loader?jquery,jquery.immediateDescendents'
            },
            {
                test: /xblock\/runtime.v1/,
                loader: 'exports-loader?XBlock!imports-loader?XBlock=xblock/core'
            },
            {
                test: /codemirror/,
                loader: 'exports-loader?window.CodeMirror'
            },
            {
                test: /tinymce/,
                loader: 'imports-loader?this=>window'
            }
        ]
    },

    resolve: {
        extensions: ['.js', '.jsx', '.json'],
        alias: {
            AjaxPrefix: 'ajax_prefix',
            accessibility: 'accessibility_tools',
            codemirror: 'codemirror-compressed',
            datepair: 'timepicker/datepair',
            'edx-ui-toolkit': 'edx-ui-toolkit/src/',  // @TODO: some paths in toolkit are not valid relative paths
            ieshim: 'ie_shim',
            jquery: 'jquery/src/jquery',  // Use the non-diqst form of jQuery for better debugging + optimization
            'jquery.flot': 'flot/jquery.flot.min',
            'jquery.ui': 'jquery-ui.min',
            'jquery.tinymce': 'tinymce/jquery.tinymce.min',
            'jquery.inputnumber': 'html5-input-polyfills/number-polyfill',
            'jquery.qtip': 'jquery.qtip.min',
            'jquery.smoothScroll': 'jquery.smooth-scroll.min',
            'jquery.timepicker': 'timepicker/jquery.timepicker',
            'backbone.associations': 'backbone-associations/backbone-associations-min',

            // See sinon/webpack interaction weirdness:
            // https://github.com/webpack/webpack/issues/304#issuecomment-272150177
            // (I've tried every other suggestion solution on that page, this
            // was the only one that worked.)
            sinon: __dirname + '/node_modules/sinon/pkg/sinon.js',
            WordCloudMain: 'xmodule/assets/word_cloud/public/js/word_cloud_main',
        },
        modules: [
            'cms/djangoapps/pipeline_js/js',
            'cms/static',
            'cms/static/cms/js',
            'common/lib/xmodule',
            'common/lib/xmodule/xmodule/js/src',
            'common/static',
            'common/static/coffee/src',
            'common/static/common/js',
            'common/static/common/js/vendor/',
            'common/static/js/src',
            'common/static/js/vendor/',
            'common/static/js/vendor/jQuery-File-Upload/js/',
            'common/static/js/vendor/tinymce/js/tinymce',
            'node_modules',
            'common/static/xmodule',
        ]
    },

    resolveLoader: {
        alias: {
            text: 'raw-loader'  // Compatibility with RequireJSText's text! loader, uses raw-loader under the hood
        }
    },

    externals: {
        backbone: 'Backbone',
        coursetalk: 'CourseTalk',
        gettext: 'gettext',
        jquery: 'jQuery',
        logger: 'Logger',
        underscore: '_',
        URI: 'URI',
        XModule: 'XModule',
        XBlockToXModuleShim: 'XBlockToXModuleShim',
    },

    watchOptions: {
        poll: true
    }
};
