// Function to fetch data from the API
async function fetchData(url) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data; // Assuming the API response is in JSON format
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Function to render a single user item
function renderUserListItem(data) {
    const listItem = document.createElement('li');
    listItem.className = 'user-item';

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar';
    const avatarImg = document.createElement('img');
    avatarImg.src = data.user.profile_image_url;
    avatarImg.alt = 'User Avatar';
    avatarDiv.appendChild(avatarImg);

    const userInfoDiv = document.createElement('div');
    userInfoDiv.className = 'user-info';
    const userNameDiv = document.createElement('div');
    userNameDiv.className = 'user-name';
    userNameDiv.textContent = data.user.name;
    userInfoDiv.appendChild(userNameDiv);

    const userScoreDiv = document.createElement('div');
    userScoreDiv.className = 'user-score';
    userScoreDiv.textContent = data.score;

    listItem.appendChild(avatarDiv);
    listItem.appendChild(userInfoDiv);
    listItem.appendChild(userScoreDiv);

    return listItem;
}

// Function to render user list
async function renderUserList() {
    const userListElement = document.getElementById('userList');
    let nextPageUrl = '/api/badges/v1/leaderboard/';

    // Variable to track if data is currently being fetched to avoid multiple simultaneous requests
    let fetchingData = false;

    async function fetchAndRenderNextPage() {
        fetchingData = true;

        // Fetch the next set of data
        if (nextPageUrl){
            const nextPageData = await fetchData(nextPageUrl);

            if (nextPageData.results && Array.isArray(nextPageData.results)) {
                nextPageData.results.forEach(user => {
                    // Create and append list items for the next set of data
                    const listItem = renderUserListItem(user);
                    userListElement.appendChild(listItem);
                });

                // Update the next page URL
                nextPageUrl = nextPageData.next;
            }

            fetchingData = false;
        }     
    }

    // Initial rendering
    await fetchAndRenderNextPage();

    // Add event listener to window scroll
    window.addEventListener('scroll', async () => {
        // Check if user has scrolled to the bottom
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000 && !fetchingData) {
            await fetchAndRenderNextPage();
        }
    });
}

// Call the function to render the initial user list when the page loads
document.addEventListener('DOMContentLoaded', renderUserList);
