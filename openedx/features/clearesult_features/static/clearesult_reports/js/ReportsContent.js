import React, { useState, useEffect } from 'react'
import Cookies from "js-cookie";
import HttpClient from "../../continuing_education/js/client";

function ReportsContent() {
    const [ sites, setSites ] = useState([]);
    const [ selectedSite, setSelectedSite ] = useState({});
    const [ filteredCourses, setFilteredCourses ] = useState([]);
    const [ courseReportLink, setCourseReportLink ] = useState("");
    const [ siteReportLink, setSiteReportLink ] = useState("");
    const [ courseBtnState, setCourseBtnState ] = useState(false);
    const [ siteBtnState, setSiteBtnState ] = useState(false);


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
                setSiteReportLink(formatReportLink(data[0].course_id, site.domain));
                setCourseReportLink(formatReportLink(data[0].course_id, site.domain));
                setSiteBtnState(true);
                setCourseBtnState(true);
            } else {
                setCourseReportLink("");
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

    const handleSiteSelect = (event) => {
        let site = getSiteObject(event);
        setSelectedSite(site);
        setSiteBtnState(false);
        setCourseBtnState(false);
        loadSiteLinkedCourses(site);
    }

    const handleCourseSelect = (courseId) => {
        setCourseReportLink(formatReportLink(courseId, selectedSite.domain));
        setCourseBtnState(true);
    }

    useEffect(() => {
        loadSites();
    }, [])

    return (
        <div className="clearesult-reports">
            <div className="clearesult-reports-main">
                <div>
                    <h3>Find a report for the entire site:</h3>
                    <select className="form-control" onChange={handleSiteSelect}>
                        {
                            sites.map((site) => <option key={site.id} value={site.id}>{site.domain}</option>)
                        }
                    </select>
                    <a href={siteReportLink} className={`btn btn-primary ${siteBtnState ? "" : "disabled"}`}>Go</a>
                </div>
                <div>
                    <h3>Or find a report for a specific course:</h3>
                    <select className="form-control" onChange={(e) => handleCourseSelect(e.target.value)}>
                        {filteredCourses.map((course) => <option key={course.course_id} value={course.course_id}>{course.course_name}</option>)}
                    </select>
                    <a href={courseReportLink} className={`btn btn-primary ${courseBtnState ? "" : "disabled"}`}>Go</a>
                </div>
            </div>
        </div>
    )
}

export default ReportsContent
