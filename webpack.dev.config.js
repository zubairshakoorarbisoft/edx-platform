/* eslint-env node */

'use strict';

var Merge = require('webpack-merge');
var path = require('path');
var webpack = require('webpack');

var commonConfig = require('./webpack.common.config.js');

module.exports = Merge.smart(commonConfig, {
    output: {
        filename: '[name].js'
    },
    devtool: 'source-map',
    plugins: [
        new webpack.LoaderOptionsPlugin({
            debug: true
        }),
        new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify('development')
        })
    ],
    module: {
        rules: [
            {
                test: /(.scss|.css)$/,
                include: [
                    /studio-frontend/,
                    /paragon/,
                    /font-awesome/
                ],
                use: [
                    'style-loader',
                    {
                        loader: 'css-loader',
                        options: {
                            sourceMap: true,
                            modules: true,
                            localIdentName: '[local]',
                            importLoaders: 1
                        }
                    },
                    {
                        loader: 'postcss-loader',
                        options: {
                            sourceMap: true,
                            ident: 'postcss',
                            plugins: function() {
                                return [
                                    require('postcss-initial')(),
                                    require('postcss-prepend-selector')({selector: '.SFE '})
                                ];
                            }
                        }
                    },
                    {
                        loader: 'sass-loader',
                        options: {
                            data: '$base-rem-size: 0.625; @import "paragon-reset";',
                            includePaths: [
                                path.join(__dirname, './node_modules/@edx/paragon/src/utils'),
                                path.join(__dirname, './node_modules/@edx/studio-frontend/src'),
                                path.join(__dirname, './node_modules/')
                            ],
                            sourceMap: true
                        }
                    }
                ]
            }
        ]
    },
    watchOptions: {
        ignored: [/node_modules/, /\.git/]
    }
});
