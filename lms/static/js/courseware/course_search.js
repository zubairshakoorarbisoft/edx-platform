$(document).ready(function() {
    let courseLibraryItems = document.getElementsByClassName('course');
    let courseMetaTags = [];
    var courseLibraryIndices = {};
    let adjuster = 1;
    for (let courseItem of courseLibraryItems) {
        courseLibraryIndices[courseItem.getAttribute('aria-label') + adjuster] = courseItem.parentElement;
        courseMetaTags[courseItem.getAttribute('aria-label') + adjuster] = courseItem.getAttribute('aria-tags');
        adjuster++;
    }

    const insensitiveSearch = (substring, string) => {
        return string.toLowerCase().indexOf(substring.toLowerCase()) !== -1;
    }

    const filterCourses = (courseLibraryIndices, searchKey) => {
        let courseKeys = Object.keys(courseLibraryIndices);
        let filteredCourses = [];
        for (let courseKey of courseKeys) {
            if (insensitiveSearch(searchKey, courseKey)
                || insensitiveSearch(searchKey, courseMetaTags[courseKey])) {
                filteredCourses.push(courseKey);
            }
        }
        return filteredCourses;
    }

    const handleCourseLibrarySearch = () => {

        let searchKey = $("#course-library-search-field").val().trim();
        if (searchKey === "") {
            return;
        }

        $("#cancel-course-library-search").removeClass("hidden");
        $(".courses-listing").empty();

        let filteredCourses = filterCourses(courseLibraryIndices, searchKey);
        if (filteredCourses.length < 1) {
            $("#no-search-results").toggleClass('no-search-result');
            $("#no-search-results").toggleClass('hidden');
        }

        for (let courseKey of filteredCourses) {
            $(".courses-listing").append(courseLibraryIndices[courseKey]);
        }
    }

    $(document).on("click", "#course-library-search-button", function() {
        handleCourseLibrarySearch();
    });

    $(document).on("keypress", "#course-library-search-field", function(e) {
        if(e.which == 13) {
            handleCourseLibrarySearch();
        }
    });

    $(document).on("click", "#cancel-course-library-search", function() {
        $("#cancel-course-library-search").toggleClass("hidden");
        $("#course-library-search-field").val("");
        $(".courses-listing").empty();
        $("#no-search-results").toggleClass('no-search-result');
        $("#no-search-results").toggleClass('hidden');
        $("#no-search-results").css({display: 'none'});
        let courseKeys = Object.keys(courseLibraryIndices);
        for (let courseKey of courseKeys) {
            $(".courses-listing").append(courseLibraryIndices[courseKey]);
        }
    });
});
