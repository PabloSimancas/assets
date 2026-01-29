import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/apiClient";
import { AssetSummary } from "../types";

export const useAssets = () => {
    return useQuery<AssetSummary[]>({
        queryKey: ["assets"],
        queryFn: async () => {
            const { data } = await apiClient.get("/assets/");
            return data;
        },
    });
};
