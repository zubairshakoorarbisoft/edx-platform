import React from "react";
import ProviderField from "./ProviderField";

export default function ProviderUpdateForm({ profiles, handleUpdateProvider, handleDeleteProvider }) {
    return (
        <div>
            <h2>Update existing IDs</h2>
            <div className="education-provider-ids">
                <div className="text-center">
                    {profiles.length ? (
                        profiles.map((profile) => (
                            <div key={profile.id} className="row m-5">
                                <ProviderField
                                    id={profile.id}
                                    providerId={profile.credit_id}
                                    providerName={profile.credit_type_details.name}
                                    handleDelete={handleDeleteProvider}
                                    handleUpdate={handleUpdateProvider}
                                />
                            </div>
                        ))
                    ) : (
                        <h4>No existing profiles found!</h4>
                    )}
                </div>
            </div>
        </div>
    );
}
