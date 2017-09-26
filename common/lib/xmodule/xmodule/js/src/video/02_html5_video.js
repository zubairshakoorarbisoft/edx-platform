/* eslint-disable no-console, no-param-reassign */
/**
 * @file HTML5 video player module. Provides methods to control the in-browser
 * HTML5 video player.
 *
 * The goal was to write this module so that it closely resembles the YouTube
 * API. The main reason for this is because initially the edX video player
 * supported only YouTube videos. When HTML5 support was added, for greater
 * compatibility, and to reduce the amount of code that needed to be modified,
 * it was decided to write a similar API as the one provided by YouTube.
 *
 * @external RequireJS
 *
 * @module HTML5Video
 */

(function(requirejs, require, define) {
    define(
'video/02_html5_video.js',
['underscore'],
function(_) {
    var HTML5Video = {};

    HTML5Video.Player = (function() {
        /*
         * Constructor function for HTML5 Video player.
         *
         * @param {String|Object} el A DOM element where the HTML5 player will
         * be inserted (as returned by jQuery(selector) function), or a
         * selector string which will be used to select an element. This is a
         * required parameter.
         *
         * @param config - An object whose properties will be used as
         * configuration options for the HTML5 video player. This is an
         * optional parameter. In the case if this parameter is missing, or
         * some of the config object's properties are missing, defaults will be
         * used. The available options (and their defaults) are as
         * follows:
         *
         *     config = {
         *
         *        videoSources: [],   // An array with properties being video
         *                            // sources. The property name is the
         *                            // video format of the source. Supported
         *                            // video formats are: 'mp4', 'webm', and
         *                            // 'ogg'.
         *        poster:             Video poster URL
         *
         *        browserIsSafari:    Flag to tell if current browser is Safari
         *
         *        events: {           // Object's properties identify the
         *                            // events that the API fires, and the
         *                            // functions (event listeners) that the
         *                            // API will call when those events occur.
         *                            // If value is null, or property is not
         *                            // specified, then no callback will be
         *                            // called for that event.
         *
         *              onReady: null,
         *              onStateChange: null
         *          }
         *     }
         */
        function Player(el, config) {
            var errorMessage, lastSource, sourceList;

            // Create HTML markup for individual sources of the HTML5 <video> element.
            sourceList = $.map(config.videoSources, function(source) {
                return [
                    '<source ',
                    'src="', source,
            // Following hack allows to open the same video twice
            // https://code.google.com/p/chromium/issues/detail?id=31014
            // Check whether the url already has a '?' inside, and if so,
            // use '&' instead of '?' to prevent breaking the url's integrity.
                        (source.indexOf('?') === -1 ? '?' : '&'),
                    (new Date()).getTime(), '" />'
                ].join('');
            });

            // do common initialization independent of player type
            this.init(el, config);

            // Create HTML markup for the <video> element, populating it with
            // sources from previous step. Set playback not supported error message.
            errorMessage = [
                gettext('This browser cannot play .mp4, .ogg, or .webm files.'),
                gettext('Try using a different browser, such as Google Chrome.')
            ].join('');
            this.video.innerHTML = sourceList.join('') + errorMessage;

            lastSource = this.videoEl.find('source').last();
            lastSource.on('error', this.showErrorMessage.bind(this));
            lastSource.on('error', this.onError.bind(this));
            this.videoEl.on('error', this.onError.bind(this));
        }

        Player.prototype.callStateChangeCallback = function() {
            if ($.isFunction(this.config.events.onStateChange)) {
                this.config.events.onStateChange({
                    data: this.playerState
                });
            }
        };

        Player.prototype.pauseVideo = function() {
            this.video.pause();
        };

        Player.prototype.seekTo = function(value) {
            if (
                typeof value === 'number' &&
                value <= this.video.duration &&
                value >= 0
            ) {
                this.video.currentTime = value;
            }
        };

        Player.prototype.setVolume = function(value) {
            if (typeof value === 'number' && value <= 100 && value >= 0) {
                this.video.volume = value * 0.01;
            }
        };

        Player.prototype.getCurrentTime = function() {
            return this.video.currentTime;
        };

        Player.prototype.playVideo = function() {
            this.video.play();
        };

        Player.prototype.getPlayerState = function() {
            return this.playerState;
        };

        Player.prototype.getVolume = function() {
            return this.video.volume;
        };

        Player.prototype.getDuration = function() {
            if (isNaN(this.video.duration)) {
                return 0;
            }

            return this.video.duration;
        };

        Player.prototype.setPlaybackRate = function(value) {
            var newSpeed;

            newSpeed = parseFloat(value);

            if (isFinite(newSpeed)) {
                if (this.video.playbackRate !== value) {
                    this.video.playbackRate = value;
                }
            }
        };

        Player.prototype.getAvailablePlaybackRates = function() {
            return [0.75, 1.0, 1.25, 1.5];
        };

        // eslint-disable-next-line no-underscore-dangle
        Player.prototype._getLogs = function() {
            return this.logs;
        };

        Player.prototype.showErrorMessage = function(event, css) {
            var cssSelecter = css || '.video-player .video-error';
            this.el
                .find('.video-player div')
                    .addClass('hidden')
                .end()
                .find(cssSelecter)
                    .removeClass('is-hidden')
                .end()
                    .addClass('is-initialized')
                .find('.spinner')
                    .attr({
                        'aria-hidden': 'true',
                        tabindex: -1
                    });
        };

        Player.prototype.onError = function() {
            if ($.isFunction(this.config.events.onError)) {
                this.config.events.onError();
            }
        };

        Player.prototype.destroy = function() {
            this.video.removeEventListener('loadedmetadata', this.onLoadedMetadata, false);
            this.video.removeEventListener('play', this.onPlay, false);
            this.video.removeEventListener('playing', this.onPlaying, false);
            this.video.removeEventListener('pause', this.onPause, false);
            this.video.removeEventListener('ended', this.onEnded, false);
            this.el
                .find('.video-player div')
                .removeClass('is-hidden')
                .end()
                .find('.video-player .video-error')
                .addClass('is-hidden')
                .end()
                .removeClass('is-initialized')
                .find('.spinner')
                .attr({'aria-hidden': 'false'});
            this.videoEl.off('remove');
            this.videoEl.remove();
        };

        Player.prototype.onLoadedMetadata = function() {
            this.playerState = HTML5Video.PlayerState.PAUSED;
            if ($.isFunction(this.config.events.onReady)) {
                this.config.events.onReady(null);
                this.videoOverlayEl.removeClass('is-hidden');
            }
        };

        Player.prototype.onPlay = function() {
            this.playerState = HTML5Video.PlayerState.BUFFERING;
            this.callStateChangeCallback();
            this.videoOverlayEl.addClass('is-hidden');
        };

        Player.prototype.onPlaying = function() {
            this.playerState = HTML5Video.PlayerState.PLAYING;
            this.callStateChangeCallback();
            this.videoOverlayEl.addClass('is-hidden');
        };

        Player.prototype.onPause = function() {
            this.playerState = HTML5Video.PlayerState.PAUSED;
            this.callStateChangeCallback();
            this.videoOverlayEl.removeClass('is-hidden');
        };

        Player.prototype.onEnded = function() {
            this.playerState = HTML5Video.PlayerState.ENDED;
            this.callStateChangeCallback();
        };

        Player.prototype.init = function(el, config) {
            var isTouch = window.onTouchBasedDevice() || '',
                events = ['loadstart', 'progress', 'suspend', 'abort', 'error',
                    'emptied', 'stalled', 'play', 'pause', 'loadedmetadata',
                    'loadeddata', 'waiting', 'playing', 'canplay', 'canplaythrough',
                    'seeking', 'seeked', 'timeupdate', 'ended', 'ratechange',
                    'durationchange', 'volumechange'
                ],
                self = this,
                callback;

            this.config = config;
            this.logs = [];
            this.el = $(el);

            // Because of problems with creating video element via jquery
            // (http://bugs.jquery.com/ticket/9174) we create it using native JS.
            this.video = document.createElement('video');

            // Get the jQuery object and set error event handlers
            this.videoEl = $(this.video);

            // Video player overlay play button
            this.videoOverlayEl = this.el.find('.video-wrapper .btn-play');

            // The player state is used by other parts of the VideoPlayer to
            // determine what the video is currently doing.
            this.playerState = HTML5Video.PlayerState.UNSTARTED;

            _.bindAll(this, 'onLoadedMetadata', 'onPlay', 'onPlaying', 'onPause', 'onEnded');

            // Attach a 'click' event on the <video> element. It will cause the
            // video to pause/play.
            callback = function() {
                var PlayerState = HTML5Video.PlayerState;

                if (self.playerState === PlayerState.PLAYING) {
                    self.playerState = PlayerState.PAUSED;
                    self.pauseVideo();
                } else {
                    self.playerState = PlayerState.PLAYING;
                    self.playVideo();
                }
            };
            this.videoEl.on('click', callback);
            this.videoOverlayEl.on('click', callback);

            this.debug = false;
            $.each(events, function(index, eventName) {
                self.video.addEventListener(eventName, function() {
                    self.logs.push({
                        'event name': eventName,
                        state: self.playerState
                    });

                    if (self.debug) {
                        console.log(
                            'event name:', eventName,
                            'state:', self.playerState,
                            'readyState:', self.video.readyState,
                            'networkState:', self.video.networkState
                        );
                    }

                    el.trigger('html5:' + eventName, arguments);
                });
            });

            // When the <video> tag has been processed by the browser, and it
            // is ready for playback, notify other parts of the VideoPlayer,
            // and initially pause the video.
            this.video.addEventListener('loadedmetadata', this.onLoadedMetadata, false);
            this.video.addEventListener('play', this.onPlay, false);
            this.video.addEventListener('playing', this.onPlaying, false);
            this.video.addEventListener('pause', this.onPause, false);
            this.video.addEventListener('ended', this.onEnded, false);

            if (/iP(hone|od)/i.test(isTouch[0])) {
                this.videoEl.prop('controls', true);
            }

            // Set video poster
            if (this.config.poster) {
                this.videoEl.prop('poster', this.config.poster);
            }

            // Place the <video> element on the page.
            this.videoEl.appendTo(el.find('.video-player > div:first-child'));

            // $.getScript('https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1');
            window['__onGCastApiAvailable'] = this.onGCastApiAvailable.bind(this);
        };

        Player.prototype.onGCastApiAvailable = function (isAvailable) {
            debugger;

            if (isAvailable) {
                cast.framework.CastContext.getInstance().setOptions({
                    receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,
                    autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED
                });

                this.remotePlayer = new cast.framework.RemotePlayer();
                this.remotePlayerController = new cast.framework.RemotePlayerController(this.remotePlayer);
                this.remotePlayerController.addEventListener(
                    cast.framework.RemotePlayerEventType.IS_CONNECTED_CHANGED,
                    this.switchPlayer.bind(this)
                );
            }
        };

        Player.prototype.switchPlayer = function () {
            // this.stopProgressTimer();
            // this.resetVolumeSlider();
            // this.playerHandler.stop();
            // this.playerState = PLAYER_STATE.IDLE;
            if (cast && cast.framework) {
                if (this.remotePlayer.isConnected) {
                    this.setupRemotePlayer();
                    return;
                }
            }
            this.setupLocalPlayer();
        };

        /**
         * Makes human-readable message from chrome.cast.Error
         * @param {chrome.cast.Error} error
         * @return {string} error message
         */
        Player.getErrorMessage = function (error) {
            switch (error.code) {
                case chrome.cast.ErrorCode.API_NOT_INITIALIZED:
                    return 'The API is not initialized.' +
                        (error.description ? ' :' + error.description : '');
                case chrome.cast.ErrorCode.CANCEL:
                    return 'The operation was canceled by the user' +
                        (error.description ? ' :' + error.description : '');
                case chrome.cast.ErrorCode.CHANNEL_ERROR:
                    return 'A channel to the receiver is not available.' +
                        (error.description ? ' :' + error.description : '');
                case chrome.cast.ErrorCode.EXTENSION_MISSING:
                    return 'The Cast extension is not available.' +
                        (error.description ? ' :' + error.description : '');
                case chrome.cast.ErrorCode.INVALID_PARAMETER:
                    return 'The parameters to the operation were not valid.' +
                        (error.description ? ' :' + error.description : '');
                case chrome.cast.ErrorCode.RECEIVER_UNAVAILABLE:
                    return 'No receiver was compatible with the session request.' +
                        (error.description ? ' :' + error.description : '');
                case chrome.cast.ErrorCode.SESSION_ERROR:
                    return 'A session could not be created, or a session was invalid.' +
                        (error.description ? ' :' + error.description : '');
                case chrome.cast.ErrorCode.TIMEOUT:
                    return 'The operation timed out.' +
                        (error.description ? ' :' + error.description : '');
            }
        };

        Player.prototype.setupRemotePlayer = function () {
            var castSession = cast.framework.CastContext.getInstance().getCurrentSession();

            // Add event listeners for player changes which may occur outside sender app
            this.remotePlayerController.addEventListener(
                cast.framework.RemotePlayerEventType.IS_PAUSED_CHANGED,
                function () {
                    if (this.remotePlayer.isPaused) {
                        this.onPause();
                    } else {
                        this.onPlay();
                    }
                }.bind(this)
            );

            // this.remotePlayerController.addEventListener(
            //     cast.framework.RemotePlayerEventType.IS_MUTED_CHANGED,
            //     function () {
            //         if (this.remotePlayer.isMuted) {
            //             this.playerHandler.mute();
            //         } else {
            //             this.playerHandler.unMute();
            //         }
            //     }.bind(this)
            // );
            //
            // this.remotePlayerController.addEventListener(
            //     cast.framework.RemotePlayerEventType.VOLUME_LEVEL_CHANGED,
            //     function () {
            //         var newVolume = this.remotePlayer.volumeLevel * FULL_VOLUME_HEIGHT;
            //         var p = document.getElementById('audio_bg_level');
            //         p.style.height = newVolume + 'px';
            //         p.style.marginTop = -newVolume + 'px';
            //     }.bind(this)
            // );

            // This object will implement PlayerHandler callbacks with
            // remotePlayerController, and makes necessary UI updates specific
            // to remote playback
            var playerTarget = {};

            playerTarget.play = function () {
                if (this.remotePlayer.isPaused) {
                    this.remotePlayerController.playOrPause();
                }

                var vi = document.getElementById('video_image');
                vi.style.display = 'block';
                var localPlayer = document.getElementById('video_element');
                localPlayer.style.display = 'none';
            }.bind(this);

            playerTarget.pause = function () {
                if (!this.remotePlayer.isPaused) {
                    this.remotePlayerController.playOrPause();
                }
            }.bind(this);

            playerTarget.stop = function () {
                this.remotePlayerController.stop();
            }.bind(this);

            playerTarget.load = function (mediaIndex) {
                console.log('Loading...' + this.mediaContents[mediaIndex]['title']);
                var mediaInfo = new chrome.cast.media.MediaInfo(this.config.videoSources[0], 'video/mp4');

                mediaInfo.metadata = new chrome.cast.media.GenericMediaMetadata();
                mediaInfo.metadata.metadataType = chrome.cast.media.MetadataType.GENERIC;
                // mediaInfo.metadata.title = this.mediaContents[mediaIndex]['title'];
                // mediaInfo.metadata.images = [
                //     {'url': MEDIA_SOURCE_ROOT + this.mediaContents[mediaIndex]['thumb']}];

                var request = new chrome.cast.media.LoadRequest(mediaInfo);
                castSession.loadMedia(request).then(
                    this.playerHandler.loaded.bind(this.playerHandler),
                    function (errorCode) {
                        this.playerState = PLAYER_STATE.ERROR;
                        console.log('Remote media load error: ' +
                            Player.getErrorMessage(errorCode));
                    }.bind(this));
            }.bind(this);

            playerTarget.getCurrentMediaTime = function () {
                return this.remotePlayer.currentTime;
            }.bind(this);

            playerTarget.getMediaDuration = function () {
                return this.remotePlayer.duration;
            }.bind(this);

            playerTarget.updateDisplayMessage = function () {
                document.getElementById('playerstate').style.display = 'block';
                document.getElementById('playerstatebg').style.display = 'block';
                document.getElementById('video_image_overlay').style.display = 'block';
                document.getElementById('playerstate').innerHTML =
                    this.mediaContents[this.currentMediaIndex]['title'] + ' ' +
                    this.playerState + ' on ' + castSession.getCastDevice().friendlyName;
            }.bind(this);

            playerTarget.setVolume = function (volumeSliderPosition) {
                // Add resistance to avoid loud volume
                var currentVolume = this.remotePlayer.volumeLevel;
                var p = document.getElementById('audio_bg_level');
                if (volumeSliderPosition < FULL_VOLUME_HEIGHT) {
                    var vScale = this.currentVolume * FULL_VOLUME_HEIGHT;
                    if (volumeSliderPosition > vScale) {
                        volumeSliderPosition = vScale + (pos - vScale) / 2;
                    }
                    p.style.height = volumeSliderPosition + 'px';
                    p.style.marginTop = -volumeSliderPosition + 'px';
                    currentVolume = volumeSliderPosition / FULL_VOLUME_HEIGHT;
                } else {
                    currentVolume = 1;
                }
                this.remotePlayer.volumeLevel = currentVolume;
                this.remotePlayerController.setVolumeLevel();
            }.bind(this);

            playerTarget.mute = function () {
                if (!this.remotePlayer.isMuted) {
                    this.remotePlayerController.muteOrUnmute();
                }
            }.bind(this);

            playerTarget.unMute = function () {
                if (this.remotePlayer.isMuted) {
                    this.remotePlayerController.muteOrUnmute();
                }
            }.bind(this);

            playerTarget.isMuted = function () {
                return this.remotePlayer.isMuted;
            }.bind(this);

            playerTarget.seekTo = function (time) {
                this.remotePlayer.currentTime = time;
                this.remotePlayerController.seek();
            }.bind(this);

            this.playerHandler.setTarget(playerTarget);

            // Setup remote player volume right on setup
            // The remote player may have had a volume set from previous playback
            if (this.remotePlayer.isMuted) {
                this.playerHandler.mute();
            }
            var currentVolume = this.remotePlayer.volumeLevel * FULL_VOLUME_HEIGHT;
            var p = document.getElementById('audio_bg_level');
            p.style.height = currentVolume + 'px';
            p.style.marginTop = -currentVolume + 'px';

            this.hideFullscreenButton();

            this.playerHandler.play();
        };

        return Player;
    }());

    // The YouTube API presents several constants which describe the player's
    // state at a given moment. HTML5Video API will copy these constants so
    // that code which uses both the YouTube API and this API doesn't have to
    // change.
    HTML5Video.PlayerState = {
        UNSTARTED: -1,
        ENDED: 0,
        PLAYING: 1,
        PAUSED: 2,
        BUFFERING: 3,
        CUED: 5
    };

    // HTML5Video object - what this module exports.
    return HTML5Video;
});
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
