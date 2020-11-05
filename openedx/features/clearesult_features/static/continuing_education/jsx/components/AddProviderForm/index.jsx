import React, { useState, useEffect } from "react";

export default function AddProviderForm({ choices, handleAddProvider }) {
    const [selected, setSelected] = useState("");
    const [providerId, setProviderId] = useState("");

    useEffect(() => {
        if (choices.length) {
            setSelected(choices[0].id);
        }
    }, [choices]);

    function handleOnClick() {
        handleAddProvider(selected, providerId);
        setProviderId("");
    }

    function handleProviderIdChange(event) {
        const newValue = event.target.value;
        if (newValue.length >= 20) return;
        setProviderId(newValue);
    }

    return (
        <div>
            <h2>Add a new ID</h2>
            <div className="form-holder">
                {choices.length ? (
                    <div className="form-area">
                        <label>Provider</label>
                        <select
                            required
                            name="provider"
                            id="provider"
                            value={selected}
                            onChange={(e) => setSelected(e.target.value)}
                        >
                            {choices &&
                                choices.map((provider) => (
                                    <option key={provider.id} value={provider.id}>
                                        {provider.name}
                                    </option>
                                ))}
                        </select>
                        <label>ID</label>
                        <input
                            required
                            placeholder="Provider ID"
                            value={providerId}
                            onChange={handleProviderIdChange}
                        ></input>
                        <button
                            disabled={choices.length === 0 || !providerId.trim()}
                            className="btn btn-primary"
                            onClick={handleOnClick}
                        >
                            Add
                        </button>
                    </div>
                ) : (
                    <div>
                        <h4>No new provider is available at the moment.</h4>
                    </div>
                )}
            </div>
        </div>
    );
}
