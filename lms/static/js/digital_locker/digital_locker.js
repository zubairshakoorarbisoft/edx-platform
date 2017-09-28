$('.digital-locker-container .digital-locker-dropdown').on('click', function(e) {
    // Grab file view container
    $fileViewerContainer = $(e.target).parent().find('.file-viewer-container');
    if (JSON.parse($fileViewerContainer.data('in-progress'))) return;
    if ($fileViewerContainer.is(":visible")) {
        $fileViewerContainer.hide();
    } else {
        // Only allow one file viewer at a time
        $('.file-viewer-container').hide();
        $fileViewerContainer.show();
    }
    $fileViewerContainer.data('in-progress', 'true');
    setTimeout(function(){
        $fileViewerContainer.data('in-progress', 'false');
    }, 50);
});

$('.file-viewer-container .close').on('click', function(e) {
    $fileViewerContainer = $(e.target).closest('.file-viewer-container');
    $fileViewerContainer.hide();
});