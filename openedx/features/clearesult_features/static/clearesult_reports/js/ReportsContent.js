import React, { useState, useEffect } from 'react'
import Cookies from "js-cookie";
import HttpClient from "../../continuing_education/js/client";

function ReportsContent() {
    const [ sites, setSites ] = useState([]);
    const [ selectedSite, setSelectedSite ] = useState(0);
    const [ filteredCourses, setFilteredCourses ] = useState([]);
    const [ reportLink, setReportLink ] = useState("");


    const client = new HttpClient({
        headers: {
            "X-CSRFToken": Cookies.get("csrftoken"),
        },
    });

    const loadSites = async () => {
        try {
            let data = (await client.get(context.SITES_URL)).data;
            setSites(data);
            setSelectedSite(data[0].id);
        } catch (exp) {
            console.log(exp);
        }
    }

    const loadSiteLinkedCourses = async (site) => {
        try {
            let data = (await client.get(context.SITE_LINKED_COURSES_URL + site)).data;
            setFilteredCourses(data);
            if (data.length > 0) {
                setReportLink(formatCourseReportLink(data[0].course_id));
            } else {
                setReportLink("");
            }
        } catch (exp) {
            console.log(exp);
        }
    }

    const formatCourseReportLink = (course_id) => {
        let url = `/courses/${course_id}/instructor#view-data_download`
        return url;
    }

    const handleSiteSelect = (value) => {
        if(!isNaN(value)) {
            setSelectedSite(value);
            loadSiteLinkedCourses(value);
        } else {
            setSelectedSite(0);
            setReportLink("");
            setFilteredCourses([
                {
                    course_id: "----",
                    course_name: "----"
                }
            ])
        }
    }

    const handleCourseSelect = (value) => {
        setReportLink(formatCourseReportLink(value));
    }

    useEffect(() => {
        loadSites();
    }, [])

    return (
        <div className="clearesult-reports">
            <div className="clearesult-reports-main">
                <h3>Select site:</h3>
                <select className="form-control" onChange={(e) => handleSiteSelect(e.target.value)}>
                    <option value="----">----</option>
                    {
                        sites.map((site) => <option key={site.id} value={site.id}>{site.domain}</option>)
                    }
                </select>
                <h3>Please select the course you want to report on:</h3>
                <select className="form-control" onChange={(e) => handleCourseSelect(e.target.value)}>
                    {filteredCourses.map((course) => <option key={course.course_id} value={course.course_id}>{course.course_name}</option>)}
                    {filteredCourses.length === 0 ? <option value="----">----</option> : ""}
                </select>
                <a href={reportLink} className="btn btn-primary">Get Report</a>
            </div>
        </div>
    )
}

export default ReportsContent
