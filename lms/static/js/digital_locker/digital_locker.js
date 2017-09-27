$('.digital-locker-dropdown').on('click', function(e) {
    // Only allow one file viewer at a time
    $('.file-viewer-container').hide()

    // Show file view
    $fileViewerContainer = $(e.target).parent().find('.file-viewer-container');
    $fileViewerContainer.show();
});

$('.file-viewer-container .close').on('click', function(e) {
    $fileViewerContainer = $(e.target).closest('.file-viewer-container');
    $fileViewerContainer.hide();
});