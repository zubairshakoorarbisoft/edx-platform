define([
    'jquery', 'js/collections/asset', 'js/views/assets', 'studio-frontend', 'jquery.fileupload'
], function($, AssetCollection, AssetsView, Assets) {
    'use strict';
    return function(config) {
        var assets = new AssetCollection(),
            assetsView;

        assets.url = config.assetCallbackUrl;
        assetsView = new AssetsView({
            collection: assets,
            el: $('.wrapper-assets'),
            uploadChunkSizeInMBs: config.uploadChunkSizeInMBs,
            maxFileSizeInMBs: config.maxFileSizeInMBs,
            maxFileSizeRedirectUrl: config.maxFileSizeRedirectUrl
        });
        assetsView.render();
    };
});
