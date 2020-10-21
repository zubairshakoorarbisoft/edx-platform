import React, { useEffect, useState } from "react";
import { ToastsContainer, ToastsStore } from "react-toasts";
import Cookies from "js-cookie";

import AddProviderForm from "./components/AddProviderForm";
import ProviderUpdateForm from "./components/ProviderUpdateForm";

import HttpClient from "../js/client";

export default function ContinuingEducationForm({ context }) {
    const [isLoading, setIsLoading] = useState(true);
    const [availableProviders, setAvailableProviders] = useState([]);
    const [allProviders, setAllProviders] = useState([]);
    const [userCreditProfiles, setUserCreditProfiles] = useState([]);

    const client = new HttpClient({
        headers: {
            "X-CSRFToken": Cookies.get("csrftoken"),
        },
    });

    async function loadInitialData() {
        try {
            const providers = (await client.get(context.CREDIT_PROVIDERS_LIST_URL)).data;
            const userCreditProfiles = (await client.get(context.USER_CREDIT_PROFILE_LIST_URL)).data;
            const existingUserIds = userCreditProfiles.map((profile) => profile.credit_type);
            const availableProviders = providers.filter((provider) => existingUserIds.indexOf(provider.id) < 0);

            setUserCreditProfiles(userCreditProfiles);
            setAvailableProviders(availableProviders);
            setAllProviders(providers);
            setIsLoading(false);
        } catch (e) {
            console.error(e);
        }
    }

    async function handleAddProvider(selectedProviderId, userEnteredId) {
        selectedProviderId = Number.parseInt(selectedProviderId);
        try {
            const response = await client.post(context.USER_CREDIT_PROFILE_LIST_URL, {
                credit_type: selectedProviderId,
                credit_id: userEnteredId,
            });
            const remainingProviders = availableProviders.filter((provider) => provider.id !== selectedProviderId);
            const updatedUserProfiles = [...userCreditProfiles];
            updatedUserProfiles.push({ ...response.data });
            setUserCreditProfiles(updatedUserProfiles);
            setAvailableProviders(remainingProviders);
            ToastsStore.success("Added a new credit profile.");
        } catch (ex) {
            console.error(ex);
            ToastsStore.error("Could not add a new profile.");
        }
    }

    async function handleDeleteProviderProfile(profileId) {
        try {
            const shouldDelete = confirm("Are you sure you want to delete the profile?");
            if (!shouldDelete) return;

            const response = await client.delete(`${context.USER_CREDIT_PROFILE_DETAILS_URL_PREFIX}${profileId}`);
            if (response.status === 204) {
                const remainingProfiles = userCreditProfiles.filter((profile) => profile.id !== profileId);
                const existingUserIds = remainingProfiles.map((profile) => profile.credit_type);
                const updatedAvailableProviders = allProviders.filter(
                    (provider) => existingUserIds.indexOf(provider.id) < 0
                );

                setAvailableProviders(updatedAvailableProviders);
                setUserCreditProfiles(remainingProfiles);
                ToastsStore.success("Deleted the profile successfully.");
            }
        } catch (ex) {
            console.error(ex);
            ToastsStore.error("Could not delete the profile.");
        }
    }

    async function handleUpdateProviderProfile(profileId, newCreditProviderId) {
        try {
            const response = await client.patch(`${context.USER_CREDIT_PROFILE_DETAILS_URL_PREFIX}${profileId}/`, {
                credit_id: newCreditProviderId,
            });
            ToastsStore.success("Updated the profile successfully.");
        } catch (ex) {
            console.error(ex);
            ToastsStore.error("Could not update the profile.");
        }
    }

    useEffect(() => {
        loadInitialData();
    }, []);

    return (
        <div className="edu-holder">
            <h1>Continuing Education IDs</h1>
            <div className="edu-holder-container">
                {isLoading ? (
                    <h3>Loading data...</h3>
                ) : (
                    <div>
                        <AddProviderForm choices={availableProviders} handleAddProvider={handleAddProvider} />
                        <ProviderUpdateForm
                            profiles={userCreditProfiles}
                            handleDeleteProvider={handleDeleteProviderProfile}
                            handleUpdateProvider={handleUpdateProviderProfile}
                        />
                    </div>
                )}
            </div>
            <ToastsContainer store={ToastsStore} />
        </div>
    );
}
