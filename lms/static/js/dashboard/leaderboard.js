var edx = edx || {};

(function ($) {
    'use strict';

    edx.dashboard = edx.dashboard || {};
    edx.dashboard.leaderboard = {};

    edx.dashboard.leaderboard.fetchData = function (url) {
        return new Promise(function (resolve, reject) {
            fetch(url)
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(function (data) {
                    resolve(data);
                })
                .catch(function (error) {
                    reject(error);
                });
        });
    };

    edx.dashboard.leaderboard.renderUserListItem = function (data) {
        var listItem = $('<li>').addClass('user-item');

        var avatarDiv = $('<div>').addClass('avatar');
        var avatarImg = $('<img>').attr('src', data.user.profile_image_url).attr('alt', 'User Avatar');
        avatarDiv.append(avatarImg);

        var userInfoDiv = $('<div>').addClass('user-info');
        var userNameDiv = $('<div>').addClass('user-name').text(data.user.name);
        userInfoDiv.append(userNameDiv);

        var userScoreDiv = $('<div>').addClass('user-score').text(data.score);

        listItem.append(avatarDiv, userInfoDiv, userScoreDiv);

        return listItem;
    };

    edx.dashboard.leaderboard.renderUserScore = function () {
        var userScoreElement = $("#leaderboard-user-score");
        var usernmae = $("#leaderboard-username").html();
        var userScoreURL = '/api/badges/v1/leaderboard/'.concat(usernmae);
        var fetchingScoreData = false;

        edx.dashboard.leaderboard.fetchData(userScoreURL)
            .then(function (userScoreData) {
               if (userScoreData && userScoreData.score){
                    userScoreElement.text(userScoreData.score);
               }
            })
            .catch(function (error) {
                console.error('Error fetching and rendering data:', error);
            })
            .finally(function () {
                fetchingScoreData = false;
            });
    };

    edx.dashboard.leaderboard.renderUserList = function () {
        var userListElement = $('#userList');
        var nextPageUrl = '/api/badges/v1/leaderboard/';
        var fetchingData = false;

        var fetchAndRenderNextPage = function () {
            if (nextPageUrl && !fetchingData) {
                fetchingData = true;
                edx.dashboard.leaderboard.fetchData(nextPageUrl)
                    .then(function (nextPageData) {
                        if (nextPageData.results && Array.isArray(nextPageData.results)) {
                            nextPageData.results.forEach(function (user) {
                                var listItem = edx.dashboard.leaderboard.renderUserListItem(user);
                                userListElement.append(listItem);
                            });

                            nextPageUrl = nextPageData.next;
                        }
                    })
                    .catch(function (error) {
                        console.error('Error fetching and rendering data:', error);
                    })
                    .finally(function () {
                        fetchingData = false;
                    });
            }
        };

        userListElement.scroll(function() {
            if ($(this).scrollTop() + $(this).innerHeight() >= this.scrollHeight - 1000 && !fetchingData) {
                fetchAndRenderNextPage();
            }
        });
        
        fetchAndRenderNextPage();
    };

    edx.dashboard.leaderboard.init = function() {
        edx.dashboard.leaderboard.renderUserScore();
        edx.dashboard.leaderboard.renderUserList();
    }
}(jQuery));
