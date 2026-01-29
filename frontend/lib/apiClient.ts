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
// Get API URL from Runtime Config (browser) OR Build Time Config (local/static) NOT "undefined" string
const getBaseUrl = () => {
    if (typeof window !== "undefined") {
        if (window.__ENV?.NEXT_PUBLIC_API_URL) {
            return window.__ENV.NEXT_PUBLIC_API_URL;
        }
    }
    // Fallback to strict empty string if not found, let the interceptor fix it later
    // IGNORE process.env to prevent build-time HTTP values from overriding
    return "https://assets-backend.kqhsmi.easypanel.host/api/v1";
};

const apiClient = axios.create({
    baseURL: getBaseUrl(),
    headers: {
        "Content-Type": "application/json",
    },
});

// Update base URL dynamically if it changes (e.g. after window load)
apiClient.interceptors.request.use((config) => {
    // ALWAYS check for the latest URL on every request
    if (typeof window !== "undefined" && window.__ENV?.NEXT_PUBLIC_API_URL) {
        config.baseURL = window.__ENV.NEXT_PUBLIC_API_URL;
    }
    return config;
});

export default apiClient;
