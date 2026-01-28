import axios from "axios";

const apiClient = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002/api/v1",
    headers: {
        "Content-Type": "application/json",
    },
});

export default apiClient;
