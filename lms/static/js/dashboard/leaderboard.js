var edx = edx || {};

(function ($) {
    'use strict';

    edx.dashboard = edx.dashboard || {};
    edx.dashboard.leaderboard = {};

    edx.dashboard.leaderboard.fetchData = async function (url) {
        try {
            const response = await fetch(url);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching data:', error);
        }
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

    edx.dashboard.leaderboard.renderUserList = async function () {
        var userListElement = $('#userList');
        var nextPageUrl = '/api/badges/v1/leaderboard/';
        var fetchingData = false;

        var fetchAndRenderNextPage = async function () {
            fetchingData = true;

            if (nextPageUrl) {
                try {
                    var nextPageData = await edx.dashboard.leaderboard.fetchData(nextPageUrl);

                    if (nextPageData.results && Array.isArray(nextPageData.results)) {
                        nextPageData.results.forEach(function (user) {
                            var listItem = edx.dashboard.leaderboard.renderUserListItem(user);
                            userListElement.append(listItem);
                        });

                        nextPageUrl = nextPageData.next;
                    }
                } catch (error) {
                    console.error('Error fetching and rendering data:', error);
                } finally {
                    fetchingData = false;
                }
            }
        };

        await fetchAndRenderNextPage();

        $(window).scroll(async function () {
            if ($(window).height() + $(window).scrollTop() >= $(document).height() - 1000 && !fetchingData) {
                await fetchAndRenderNextPage();
            }
        });
    };

    $(document).ready(function () {
        edx.dashboard.leaderboard.renderUserList();
    });
}(jQuery));
