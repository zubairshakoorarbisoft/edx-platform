define([
    'domReady', 'js/views/export', 'jquery', 'gettext'
], function(domReady, Export, $, gettext) {
    'use strict';
    return function(courselikeHomeUrl, library, statusUrl, directory_id='', bot_id='') {
        var $submitBtn = $('.action-export'),
            unloading = false,
            previousExport = Export.storedExport(courselikeHomeUrl);
        
        const spanElement = $('#course_unsync_value');
        const courseHomeUrlSplit = courselikeHomeUrl.split('/');
        const coursekey =  courseHomeUrlSplit[courseHomeUrlSplit.length - 1];

        const handleProgressBar = function(delta){
            const section_length =  delta.section.length;
            if (section_length !== 0){
                const percent = ((section_length - delta.delta_count) / section_length) * 100;
                $('.progress-bar span').css('width', percent + '%');
            }
        }

        var onComplete = function() {
            spanElement.removeClass('loader');
            const delta = JSON.parse(localStorage.getItem('CourseDelta'));
            spanElement.text(delta.delta_count);
            $('.action-export .btn').prop("disabled", false);
            handleProgressBar(delta);
            localStorage.setItem('poolingCount', 0);
            localStorage.setItem('poolingStatus', 2);
        };

        let StatusCheck = function(){
            $.ajax({
                type: 'GET',
                url: `/api/edly_panel/v1/integrate/chatly/`,
                data: {
                    course_key: coursekey,
                },
                success: function(result, textStatus, xhr) {
                    if (xhr.status === 200) {
                        if(result['status']===0){
                            const count =  Number.parseInt(localStorage.getItem('poolingCount'));
                            if(count<15){
                                localStorage.setItem('poolingCount', count+1);
                                setTimeout(StatusCheck, 6000);
                            }else{
                                onComplete();
                            }
                        }else{
                            console.log('Export was succesful');
                            localStorage.setItem('poolingStatus', 1);
                            localStorage.setItem('poolingCount', 0);
                            // updating the button 
                            spanElement.removeClass('loader');
                            const btn = $(".action-export .btn");
                            btn.get(0).lastChild.nodeValue = "All Caught Up";
                            btn.prop("disabled", true);
                            btn.addClass("catch-up");
                            spanElement.text("\uD83C\uDF89"); 

                            // update local storage 
                            let delta = JSON.parse(localStorage.getItem('CourseDelta'));
                            delta.delta_count= 0;
                            delta.section = delta.section.map((item)=> {
                                return {...item, modified_or_not_exist:false};
                            });
                            handleProgressBar(delta);
                            localStorage.setItem("CourseDelta", JSON.stringify(delta));
                        }
                    }else{
                        localStorage.setItem('poolingStatus', 2);
                        onComplete();
                    }
                },
                error: function(xhr, status, error) {
                    localStorage.setItem('poolingStatus', 2);
                    onComplete();
                }
            });
        }
        
        let onExportComplete = function(){
            console.log("Export have been completed successfully");
            $.ajax({
                type: 'POST',
                url: courselikeHomeUrl,
                data: {
                    "export_course":true,
                    "directory_id": directory_id,
                    "bot_id": bot_id,
                },
                success: function(result, textStatus, xhr) {
                    if (xhr.status === 200) {
                        console.log("Download successfully");
                        localStorage.setItem('poolingStatus', 0);
                        localStorage.setItem('poolingCount', 0);
                        setTimeout(StatusCheck, 6000);
                    }
                },
                error: function(xhr, status, error) {
                    localStorage.setItem('poolingStatus', 2);
                    onComplete();
                }
            });
        }

        var startExport = function(e) {
            e.preventDefault();
            Export.reset(library);
            Export.start(statusUrl).then(onExportComplete);
            spanElement.addClass('loader');
            $('.action-export .btn').prop("disabled", true);
            spanElement.text('');
            $.ajax({
                type: 'POST',
                url: `/export/${coursekey}`,
                data: {},
                success: function(result, textStatus, xhr) {
                    if (xhr.status === 200) {
                        setTimeout(function() { Export.pollStatus(result); }, 1000);
                    } else {
                        // It could be that the user is simply refreshing the page
                        // so we need to be sure this is an actual error from the server
                        if (!unloading) {
                            $(window).off('beforeunload.import');
                            Export.reset(library);
                            onComplete();
                            Export.showError(gettext('Your export has failed.'));
                        }
                    }
                },
                error: function(xhr, status, error) {
                    localStorage.setItem('poolingStatus', 2);
                    onComplete();
                }
            });
        };

        $(window).on('beforeunload', function() { unloading = true; });
        domReady(function() {
            // export form setup
            $submitBtn.bind('click', startExport);
        });
    };
});
