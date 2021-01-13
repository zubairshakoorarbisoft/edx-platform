import React from 'react';
const Table = ({
    isSuperUser,
    availableCatalogs,
    handleDeleteCatalogButton,
    handleEditCatalogButton
}) => {
    const renderHeader = () => {
        let headerElement = ['#', 'id', 'name', 'site', 'Actions']
        return headerElement.map((key, index) => {
            return <th key={index}>{key.toUpperCase()}</th>
        })
    }

    const renderBody = () => {
        if (availableCatalogs === null || availableCatalogs === [] || availableCatalogs === undefined){
            return <h1>No data available. </h1>
        }
        return availableCatalogs.map(({ id, name, site, clearesult_courses}) => {
            const div_id = "#collapse" + id
            const div_id2 = "collapse" + id
            return (
            <React.Fragment key={id}>
                <tr>
                    <td>
                        <a className="btn" data-toggle="collapse" href={div_id} role="button" aria-expanded="false" aria-controls={div_id2}>
                            <i className="fa fa-expand" aria-hidden="true"></i>
                        </a>
                    </td>
                    <td>{id}</td>
                    <td>{name}</td>
                    <td>{(site === null) ? "public" : site.domain}</td>
                    <td className="button-holder">
                        <button type="button" className="btn btn-primary" className={(site === null && isSuperUser == 0) ? "disabled" : ""} data-toggle="modal" data-target="#exampleModalCenter" value={id} onClick={(event)=>handleEditCatalogButton(event)} >
                            Edit
                        </button>
                        <button type="button" className="btn btn-danger" className={(site === null && isSuperUser == 0) ? "disabled" : ""} value={id} onClick={(event)=>handleDeleteCatalogButton(event)} >
                            Delete
                        </button>
                    </td>
                </tr>
                <tr className="hide-table-padding">
                    <td></td>
                    <td colSpan="4">
                        <div id={div_id2} className="collapse in p-3">
                            <div className="row">
                                <div className="col-2">ID</div>
                                <div className="col-3">Course Name</div>
                                <div className="col-3">Curse ID</div>
                                <div className="col-2">Site</div>
                            </div>
                            { clearesult_courses.map(({id, course_name, site, course_id}) => {
                                return (
                                    <div className="row" key={id}>
                                        <div className="col-2">{id}</div>
                                        <div className="col-3">{course_name}</div>
                                        <div className="col-3">{course_id}</div>
                                        <div className="col-2">{(site === null) ? "public" : site.domain}</div>
                                    </div>
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
            <table id='catalogs' className="table">
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
