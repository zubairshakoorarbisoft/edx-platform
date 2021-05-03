import React, { useState, useEffect } from 'react'
import Cookies from "js-cookie";
import HttpClient from "../../continuing_education/js/client";

function ReportsContent() {
    const [ sites, setSites ] = useState([]);
    const [ siteForCourseReport, setSiteForCourseReport ] = useState({});
    const [ filteredCourses, setFilteredCourses ] = useState([]);
    const [ courseReportLink, setCourseReportLink ] = useState("");
    const [ siteReportLink, setSiteReportLink ] = useState("");


    const client = new HttpClient({
        headers: {
            "X-CSRFToken": Cookies.get("csrftoken"),
        },
    });

    const loadSites = async () => {
        try {
            let data = (await client.get(context.SITES_URL)).data;
            setSites(data);
        } catch (exp) {
            console.error(exp);
        }
    }

    const loadSiteLinkedCourses = async (site) => {
        try {
            let data = (await client.get(context.SITE_LINKED_COURSES_URL + site.id)).data;
            setFilteredCourses(data);
            if (data.length > 0) {
                setCourseReportLink(formatReportLink(data[0].course_id, site.domain));
            } else {
                setCourseReportLink("");
            }
        } catch (exp) {
            console.error(exp);
        }
    }

    const loadSiteLinkedCourse = async (site) => {
        try {
            let data = (await client.get(context.SITE_LINKED_COURSE_URL + site.id)).data;
            if (data.length > 0) {
                setSiteReportLink(formatReportLink(data[0].course_id, site.domain));
            } else {
                setSiteReportLink("");
            }
        } catch (exp) {
            console.error(exp);
        }
    }

    const formatReportLink = (courseId, siteDomain) => {
        let url = `//${siteDomain}/courses/${courseId}/instructor#view-data_download`
        return url;
    }

    const getSiteObject = (event) => {
        let index = event.nativeEvent.target.selectedIndex;
        let text = event.nativeEvent.target[index].text;
        let value = event.nativeEvent.target[index].value;
        return {
            id: value,
            domain: text
        }
    }

    const handleSiteSelectForCourseReport = (event) => {
        let site = getSiteObject(event);
        if(!isNaN(site.id)) {
            setSiteForCourseReport(site);
            loadSiteLinkedCourses(site);
        } else {
            setSiteForCourseReport(site);
            setCourseReportLink("");
            setFilteredCourses([
                {
                    course_id: "----",
                    course_name: "----"
                }
            ])
        }
    }

    const handleSiteSelectForSiteReport = (event) => {
        let site = getSiteObject(event);
        if(!isNaN(site.id)) {
            loadSiteLinkedCourse(site);
        } else {
            setSiteReportLink("");
        }
    }

    const handleCourseSelect = (courseId) => {
        setCourseReportLink(formatReportLink(courseId, siteForCourseReport.domain));
    }

    useEffect(() => {
        loadSites();
    }, [])

    return (
        <div className="clearesult-reports">
            <div className="clearesult-reports-main">
                <div className="site-level-reports">
                    <h2>Site level reports</h2>
                    <h3>Select site:</h3>
                    <select className="form-control" onChange={handleSiteSelectForSiteReport}>
                        <option value="----">----</option>
                        {
                            sites.map((site) => <option key={site.id} value={site.id}>{site.domain}</option>)
                        }
                    </select>
                    <a href={siteReportLink} className="btn btn-primary">Get Report</a>
                </div>
                <div className="course-level-section">
                    <h2>Course level reports</h2>
                    <h3>Select site:</h3>
                    <select className="form-control" onChange={handleSiteSelectForCourseReport}>
                        <option value="----">----</option>
                        {
                            sites.map((site) => <option key={site.id} value={site.id}>{site.domain}</option>)
                        }
                    </select>
                    <h3>Select course:</h3>
                    <select className="form-control" onChange={(e) => handleCourseSelect(e.target.value)}>
                        <option value="----">----</option>
                        {filteredCourses.map((course) => <option key={course.course_id} value={course.course_id}>{course.course_name}</option>)}
                    </select>
                    <a href={courseReportLink} className="btn btn-primary">Get Report</a>
                </div>
            </div>
        </div>
    )
}

export default ReportsContent
