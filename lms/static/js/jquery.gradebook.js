


var Gradebook = function($element) {
    "use strict";
    var $body = $('body');
    var $grades = $element.find('.grades');
    var $studentTable = $element.find('.student-table');
    var $gradeTable = $element.find('.grade-table');
    var $search = $element.find('.student-search-field');
    var $leftShadow = $('<div class="left-shadow"></div>');
    var $rightShadow = $('<div class="right-shadow"></div>');
    var tableHeight = $gradeTable.height();
    var maxScroll = $gradeTable.width() - $grades.width();
    var $footer = $element.find('.grade-book-footer');
    var $error = $element.find('.error-state');
    var $searchForm = $element.find('.student-search');
    const gradebookElement = document.getElementById('gradebook-data');
    const context = gradebookElement ? JSON.parse(gradebookElement.textContent || '{}') : null;

    var MIN_CHARS = 3;
    var PAGE_SIZE = 20;
    var currentOffset = 0;
    var DEBOUNCE_DELAY = 500;
    var currentPage;
    var totalPages;
    var nextCursor = null;
    var searchTimeout = null;
    var prevCursor = null;
    var currentSearchTerm = '';

    var mouseOrigin;
    var tableOrigin;

    var startDrag = function(e) {
        mouseOrigin = e.pageX;
        tableOrigin = $gradeTable.position().left;
        $body.addClass('no-select');
        $body.bind('mousemove', onDragTable);
        $body.bind('mouseup', stopDrag);
    };

    /**
     * - Called when the user drags the gradetable
     * - Calculates targetLeft, which is the desired position 
     *   of the grade table relative to its leftmost position, using:
     *   - the new x position of the user's mouse pointer;
     *   - the gradebook's current x position, and;
     *   - the value of maxScroll (gradetable width - container width).
     * - Updates the position and appearance of the gradetable.
     */
    var onDragTable = function(e) {
        var offset = e.pageX - mouseOrigin;
        var targetLeft = clamp(tableOrigin + offset, maxScroll, 0);
        updateHorizontalPosition(targetLeft);
        setShadows(targetLeft);
    };

    var stopDrag = function() {
        $body.removeClass('no-select');
        $body.unbind('mousemove', onDragTable);
        $body.unbind('mouseup', stopDrag);
    };

    var setShadows = function(left) {
        var padding = 30;

        var leftPercent = clamp(-left / padding, 0, 1);
        $leftShadow.css('opacity', leftPercent);

        var rightPercent = clamp((maxScroll + left) / padding, 0, 1);
        $rightShadow.css('opacity', rightPercent);
    };

    var clamp = function(val, min, max) {
        if(val > max) { return max; }
        if(val < min) { return min; }
        return val;
    };

    /**
     * - Called when the browser window is resized.
     * - Recalculates maxScroll (gradetable width - container width).
     * - Calculates targetLeft, which is the desired position
     *   of the grade table relative to its leftmost position, using:
     *   - the gradebook's current x position, and:
     *   - the new value of maxScroll
     * - Updates the position and appearance of the gradetable.
     */
    var onResizeTable = function() {
        maxScroll = $gradeTable.width() - $grades.width();
        var targetLeft = clamp($gradeTable.position().left, maxScroll, 0);
        updateHorizontalPosition(targetLeft);
        setShadows(targetLeft);
    };

    /**
     * - Called on table drag and on window (table) resize.
     * - Takes a integer value for the desired (pixel) offset from the left
     *   (zero/origin) position of the grade table.
     * - Uses that value to position the table relative to its leftmost
     *   possible position within its container.
     *
     *   @param {Number} left - The desired pixel offset from left of the
     *     desired position. If the value is 0, the gradebook should be moved 
     *     all the way to the left side relative to its parent container.
     */
    var updateHorizontalPosition = function(left) {
        $grades.scrollLeft(left);
    };

    var highlightRow = function() {
        $element.find('.highlight').removeClass('highlight');

        var index = $(this).index();
        $studentTable.find('tr').eq(index + 1).addClass('highlight');
        $gradeTable.find('tr').eq(index + 1).addClass('highlight');
    };

    function getApiUrl(searchTerm, cursor) {
        const courseId = context.course_id;
        let url = `/api/v1/gradebook/${courseId}/?page_size=${PAGE_SIZE}`;
        
        if (searchTerm){ 
            url += `&user_contains=${encodeURIComponent(searchTerm)}`;
        }

        if (cursor) {
            url += `&cursor=${encodeURIComponent(cursor)}`;
        }
        return url;
    }

    function getGradeClass(fraction) {   
        let letterGrade = 'None';
        if (fraction > 0) {
            letterGrade = 'F';
            for (const [grade, cutoff] of context.ordered_grades) {
                if (fraction >= cutoff) {
                    letterGrade = grade;
                    break;
                }
            }
        }
        return `grade_${letterGrade}`;
    }
    
    function updateTables(data) {
        const $studentBody = $studentTable.find('tbody');
        const $gradeBody = $gradeTable.find('tbody');
        
        $studentBody.empty();
        $gradeBody.empty();
        
        if (!data.results || data.results.length === 0) {
            updatePaginationFooter(data);
            $error.show();
            $footer.hide();
            return;
        }

        $error.hide();
        $footer.show();
        data.results.forEach(student => {
            const studentUrl = context.studentProgressUrlTemplate.replace('STUDENT_ID', student.id);
            const studentRow = $(`<tr>
                <td>
                    <a href="${studentUrl}">${student.username}</a>
                </td>
            </tr>`);
            $studentBody.append(studentRow);
            let gradeRow = $('<tr>');            
            if (student.grade_summary && student.grade_summary.section_breakdown) {
                student.grade_summary.section_breakdown.forEach(section => {
                    const percent = section.percent || 0;
                    const detail = section.detail || '';
                    const gradeClass = getGradeClass(percent);

                    gradeRow.append(`<td class="${gradeClass}" data-percent="${percent}" title="${detail}">
                        ${Math.floor(percent * 100)}
                    </td>`);
                });
                
                const totalPercent = student.grade_summary.percent || 0;
                const totalGrade = getGradeClass(totalPercent);
                gradeRow.append(`<td class="${totalGrade}" data-percent="${totalPercent}" title="Total">
                    ${Math.floor(totalPercent * 100)}
                </td>`);
            }
            $gradeBody.append(gradeRow);
        });
    
        updatePaginationFooter(data);    
        $element.find('tr').unbind('mouseover').bind('mouseover', highlightRow);
        tableHeight = $gradeTable.height();
        maxScroll = $gradeTable.width() - $grades.width();
        $leftShadow.css('height', tableHeight + 'px');
        $grades.css('height', tableHeight);
        setShadows(0);
        $gradeTable.unbind('mousedown').bind('mousedown', startDrag);
    }

    function extractCursorFromUrl(url) {
        if (!url) return null;
        
        try {
            const parsedUrl = new URL(url);
            return parsedUrl.searchParams.get('cursor');
        } catch (e) {
            console.error('Failed to parse URL:', e);
            return null;
        }
    }

    function updatePaginationFooter(data) {
        nextCursor = extractCursorFromUrl(data.next);
        prevCursor = extractCursorFromUrl(data.previous);

        if (data.filtered_users_count === 0) {
            totalPages = 1;
            currentPage = 1;
        }
         else   {
            totalPages = Math.ceil(data.filtered_users_count / PAGE_SIZE);
            
            if (!prevCursor) {
                currentPage = 1;
            } else if (!nextCursor) {
                currentPage = totalPages;
            }
        }
        
        $footer.find('.current-page').text(currentPage);
        $footer.find('.total-pages').text(totalPages);
        
        if (prevCursor) {
            $footer.find('.pagination-prev')
                .attr('data-cursor', prevCursor)
                .css('visibility', 'visible')
                .show();
        } else {
            $footer.find('.pagination-prev')
                .removeAttr('data-cursor')
                .css('visibility', 'hidden')
                .hide();
        }
        
        if (nextCursor) {
            $footer.find('.pagination-next')
                .attr('data-cursor', nextCursor)
                .css('visibility', 'visible')
                .show();
        } else {
            $footer.find('.pagination-next')
                .removeAttr('data-cursor')
                .css('visibility', 'hidden')
                .hide();
        }
    }
    
    $footer.on('click', '.pagination-prev', function(event) {
        const cursor = $(this).attr('data-cursor');
        if (cursor) {
            event.preventDefault();
            if (currentPage > 1) {
                currentPage--;
            }
            performSearch(undefined, cursor);
        }
    });

    $footer.on('click', '.pagination-next', function(event) {
        const cursor = $(this).attr('data-cursor');
        if (cursor) {
            event.preventDefault();

            if (currentPage < totalPages) {
                currentPage++;
            }
            performSearch(undefined, cursor);
        }
    });

    function performSearch(searchTerm, cursor) {
        if (searchTerm !== undefined) {
            currentSearchTerm = searchTerm;
            currentPage = 1;
        }

        $searchForm.addClass('search-loading');
        $.ajax({
            url: getApiUrl(currentSearchTerm, cursor),
            method: 'GET',
            success: function(response) {
                updateTables(response);
            },
            error: function(xhr, status, error) {
                console.error('Search failed:', error);
                $studentTable.find('tbody').html('');
                $error.find('h6').text('Error loading students. Please try again.');
                $error.find('span').hide()
                $error.show();
                $footer.hide();
            },
            complete: function() {
                $searchForm.removeClass('search-loading');
            }
        });
    }

    function adjustTableHeight() {
        tableHeight = $gradeTable.height();
        $leftShadow.css('height', tableHeight + 'px');
        $grades.css('height', tableHeight);
        maxScroll = $gradeTable.width() - $grades.width();
        setShadows(0);
    }

    var filter = function(event) {
        var term = $(this).val().trim().toLowerCase();

        if(term.length > 0) {
            $studentTable.find('tbody tr').hide();
            $gradeTable.find('tbody tr').hide();
            $studentTable.find('tbody tr:contains(' + term + ')').each(function() {
                $(this).show();
                $gradeTable.find('tr').eq($(this).index() + 1).show();
            });
        } else {
            $studentTable.find('tbody tr').show();
            $gradeTable.find('tbody tr').show();
        }

        adjustTableHeight();
        
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
    
        searchTimeout = setTimeout(() => {
            if (term.length >= MIN_CHARS || event.key === 'Enter' || term.length === 0) {
                currentOffset = 0;
                performSearch(term, 0);
            }
        }, DEBOUNCE_DELAY);
    };
    

    var handleSubmit = function(event) {
        event.preventDefault();
        var term = $search.val().trim();
        if (term.length > 0) {
            currentOffset = 0;
            performSearch(term, 0);
        }
    };

    $leftShadow.css('height', tableHeight + 'px');
    $grades.append($leftShadow).append($rightShadow);
    setShadows(0);
    $grades.css('height', tableHeight);
    $gradeTable.bind('mousedown', startDrag);
    $element.find('tr').bind('mouseover', highlightRow);
    $search.bind('keyup', filter);
    $(window).bind('resize', onResizeTable);
    $searchForm.bind('submit', handleSubmit);
};




