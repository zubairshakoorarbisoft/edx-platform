import React, { useEffect, useState } from "react";
import DualListBox from 'react-dual-listbox';
export default function MandatoryCoursesConfigModal({
    alottedTime,
    setAlottedTime,
    notificationTime,
    setNotificationTime,
    title,
    updateMandatoryCoursesConfig
}) {

    const btnText = (alottedTime == "" && notificationTime =="") ? "Add": "Update";

    return (
        <div>
            <div className="modal fade modal-update" id="exampleModalCenter" tabIndex="-1" role="dialog" aria-labelledby="exampleModalCenterTitle" aria-hidden="true">
                <div className="modal-dialog modal-dialog-centered" role="document">
                    <div className="modal-content">
                        <form onSubmit={(event)=>updateMandatoryCoursesConfig(event)}>
                            <div className="modal-header">
                                <span>Configurations of <strong>{title}</strong></span>
                                <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label htmlFor="siteCourseAlottedTime">Time allotted to complete course:</label>
                                    <input type="number" className="form-control" value={alottedTime} onChange={(event) => setAlottedTime(event.target.value)} required id="siteCourseAlottedTime" aria-describedby="siteCourseAlottedTimeHelp" placeholder="Enter in Days" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="siteCourseNotificationTime">Course Notificateion period:</label>
                                    <input type="number" className="form-control" value={notificationTime} onChange={(event) => setNotificationTime(event.target.value)} required id="siteCourseNotificationTime" aria-describedby="siteCourseNotificationTime" placeholder="Enter in Days"/>
                                </div>

                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" data-dismiss="modal">Close</button>
                                <button type="submit" className="btn btn-primary">{btnText}</button>
                            </div>
                    	</form>
                	</div>
                </div>
            </div>
        </div>
    );
}
