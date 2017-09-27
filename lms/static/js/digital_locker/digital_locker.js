var is_showing = false;

$('.digital-locker-dropdown').on('click', function(e) {
    // Only allow one file viewer at a time
    $('.file-viewer-container').hide()

    // Show file view
    $fileViewerContainer = $(e.target).parent().find('.file-viewer-container');
    if (is_showing) {
        $fileViewerContainer.hide();
        is_showing = false;
    } else {
        $fileViewerContainer.show();
        is_showing = true;
    }
});

$('.file-viewer-container .close').on('click', function(e) {
    $fileViewerContainer = $(e.target).closest('.file-viewer-container');
    $fileViewerContainer.hide();
});