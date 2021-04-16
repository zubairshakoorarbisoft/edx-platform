import React, { useState, useEffect } from 'react';
import ToggleSwitch from '../components/ToggleSwitch';


const Table = ({
    groupCatalogs,
    removeCatalog,
    updateMandatoryCourses
  }) => {
    const renderHeader = () => {
        let headerElement = ['#', 'id', 'group', 'site']

        return headerElement.map((key, index) => {
            return <th key={index}>{key.toUpperCase()}</th>
        })
    }

    const renderBody = () => {
        if (!groupCatalogs || !groupCatalogs.length){
            return <tr></tr>
        }

        return groupCatalogs.map(({ id, name, site, catalogs}) => {
            const div_id = "#collapse" + id
            const div_id2 = "collapse" + id
            let group_id = id

            return (
            <React.Fragment key={id}>
                <tr>
                    <td>
                        <a className="btn" data-toggle="collapse" href={div_id} role="button" aria-expanded="false" aria-controls={div_id2}>
                          <i className="fa fa-expand" aria-hidden="true"></i>
                        </a>
                    </td>
                    <td>{id} {(id != site.default_group) ? '': <span className="badge badge-info">Default</span>}</td>
                    <td>{name}</td>
                    <td>{site.domain}</td>
                    <td>

                    </td>
                </tr>
                <tr className="hide-table-padding">
                    <td></td>
                    <td colSpan="8">
                        <div id={div_id2} className="collapse in p-3">
                            <div className="row">
                                <div  className="col-2 font-weight-bold">#</div>
                                <div className="col-3 font-weight-bold">CATALOG</div>
                                <div className="col-2 font-weight-bold">SITE</div>
                                <div className="col-2 font-weight-bold">ACTIONS</div>
                            </div>
                            <hr />
                            { catalogs.map(({id, catalog, mandatory_courses}) => {
                                const div_id_1 = "#test" + id
                                const div_id_2 = "test" + id
                                let mandatory_table_id = id
                                return (
                                    <React.Fragment key={id}>
                                    <div className="row" key={id}>
                                        <div className="col-2"><a className="btn" data-toggle="collapse" href={div_id_1} role="button" aria-expanded="false" aria-controls={div_id_2}>
                                            <i className="fa fa-chevron-right" aria-hidden="true"></i>
                                        </a></div>
                                        <div className="col-3">{catalog.name}</div>
                                        <div className="col-2">{catalog.site!=null ? catalog.site.domain: "public"}</div>
                                        <div className="col-2">
                                            <button
                                                value={group_id + ',' + catalog.id}
                                                onClick={(e) => {if (window.confirm('Are you sure you wish to remove this catalog?')) removeCatalog(e.target.value)}}
                                                className="btn btn-sm btn-primary"
                                            >
                                                Remove
                                            </button>
                                        </div>
                                    </div>
                                    <div colSpan="8">
                                        <div id={div_id_2} className="collapse in p-3">
                                            <div className="row">
                                                <div className="col-2"></div>
                                                <div className="col-3 font-weight-bold">Course ID</div>
                                                <div className="col-2 font-weight-bold">Course Name</div>
                                                <div className="col-2 font-weight-bold">Mandatory</div>
                                            </div>
                                            { catalog.clearesult_courses.map(({id, course_id, course_name}) => {
                                                let btn_text = "Make Mandatory"
                                                let action = "add"
                                                let mandatory_class_name = "btn-outline-primary"
                                                let is_mandatory = false
                                                if (mandatory_courses.includes(id)) {
                                                    mandatory_class_name = "btn-primary"
                                                    btn_text = "Remove Mandatory"
                                                    action = "remove"
                                                    is_mandatory = true
                                                }
                                                let btn_value = group_id+","+mandatory_table_id+","+id+","+action

                                                return (
                                                    <div className="row" key={id}>
                                                        <div className="col-2"></div>
                                                        <div className="col-3">{course_id}</div>
                                                        <div className="col-2">{course_name}</div>
                                                        <div className="col-2">
                                                            <ToggleSwitch
                                                                value={btn_value = group_id+","+mandatory_table_id+","+id+","+action}
                                                                updateMandatoryCourses={updateMandatoryCourses}
                                                                is_mandatory={is_mandatory}
                                                            />

                                                        </div>
                                                    </div>

                                                );
                                            })}
                                            <hr />
                                        </div>
                                    </div>
                                    </React.Fragment>

                                );
                            })}
                        </div>
                    </td>
                </tr>
            </React.Fragment>
            )}
        )
    }

    return (
        <div className="table-responsive">
            <table id='groups' className="table">
                <thead>
                    <tr>{renderHeader()}</tr>
                </thead>
                <tbody>
                    {renderBody()}
                </tbody>
            </table>
        </div>
    );
}

export default Table
