import axios from "axios";

// Declare global type for window.__ENV
declare global {
    interface Window {
        __ENV?: {
            NEXT_PUBLIC_API_URL?: string;
        };
    }
}

// Get API URL from Runtime Config (browser) OR Build Time Config (local/static) NOT "undefined" string
const getBaseUrl = () => {
    if (typeof window !== "undefined" && window.__ENV?.NEXT_PUBLIC_API_URL) {
        return window.__ENV.NEXT_PUBLIC_API_URL;
    }
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002/api/v1";
};

const apiClient = axios.create({
    baseURL: getBaseUrl(),
    headers: {
        "Content-Type": "application/json",
    },
});

// Update base URL dynamically if it changes (e.g. after window load)
if (typeof window !== "undefined") {
    apiClient.interceptors.request.use((config) => {
        const currentUrl = getBaseUrl();
        if (config.baseURL !== currentUrl) {
            config.baseURL = currentUrl;
        }
        return config;
    });
}

export default apiClient;
