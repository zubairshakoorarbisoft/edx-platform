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

    edx.dashboard.leaderboard.renderUserList = function () {
        var userListElement = $('#userList');
        var nextPageUrl = '/api/badges/v1/leaderboard/';
        var fetchingData = false;

        var fetchAndRenderNextPage = function () {
            fetchingData = true;

            if (nextPageUrl) {
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
        
        fetchAndRenderNextPage();

        userListElement.scroll(function() {
            if ($(this).scrollTop() + $(this).innerHeight() >= this.scrollHeight - 1000 && !fetchingData) {
                fetchAndRenderNextPage();
            }
        });
    };

    $(document).ready(function () {
        edx.dashboard.leaderboard.renderUserList();
    });
}(jQuery));
