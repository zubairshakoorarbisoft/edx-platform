import React, { useState, useEffect } from 'react';

const Table = ({groups, handleEditClick, DeleteGroup}) => {
    const renderHeader = () => {
        let headerElement = ['#', 'id', 'name', 'site', 'Actions']

        return headerElement.map((key, index) => {
            return <th key={index}>{key.toUpperCase()}</th>
        })
    }

    const renderBody = () => {
        if (!groups || !groups.length){
            return <tr></tr>
        }

        return groups.map(({ id, name, site, users}) => {
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
                    <td>{id} {(id != site.default_group) ? '': <span className="badge badge-info">Default</span>}</td>
                    <td>{name}</td>
                    <td>{site.domain}</td>
                    <td className="button-holder">
                        <button type="button" data-toggle="modal" data-target="#exampleModalCenter" value={id} onClick={(e)=>handleEditClick(e.target.value)} >
                            Edit
                        </button>
                        <button type="button" value={id} disabled={!(id != site.default_group)} onClick={(e)=> {if (window.confirm('Are you sure you wish to delete this item?')) DeleteGroup(e.target.value)}} >
                            Delete
                        </button>
                    </td>
                </tr>
                <tr className="hide-table-padding">
                    <td></td>
                    <td colSpan="4">
                        <div id={div_id2} className="collapse in p-3">
                            <div className="row">
                                <div className="col-2">Username</div>
                                <div className="col-6">Email</div>
                            </div>
                            { users.map(({id, username, email}) => {
                                return (
                                    <div className="row" key={id}>
                                        <div className="col-2">{username}</div>
                                        <div className="col-6">{email}</div>
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
