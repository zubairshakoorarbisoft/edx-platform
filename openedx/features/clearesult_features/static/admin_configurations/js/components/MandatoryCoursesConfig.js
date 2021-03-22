import React, {useState, useEffect} from 'react';
import Cookies from "js-cookie";


export default function MandatoryCoursesConfig({availableSites, changedSiteHandler, dueDateConfigbtnText, editBtnClickHandler}) {
    const siteOptions = availableSites.map(
        (availableSite) => {
            return <option key={availableSite.id} value={availableSite.id} >{availableSite.domain}</option>
        }
    )
    return (
        <div>
            <h2>Mandatory Courses Due Date Configurations</h2>
            <p> Site:
                <select onChange={(e) => changedSiteHandler(e.target.value)}>
                    {siteOptions}
                </select>
            </p>
            <button
                    type="button"
                    className="btn btn-primary"
                    data-toggle="modal"
                    data-target="#exampleModalCenter"
                    onClick={(event)=>{editBtnClickHandler(true)}}
                >
                    {dueDateConfigbtnText}
            </button>
        </div>
    )
}
