import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/apiClient";
import { AssetDetail } from "../types";

export const useAssetDetail = (symbol: string) => {
    return useQuery<AssetDetail>({
        queryKey: ["assets", symbol],
        queryFn: async () => {
            const { data } = await apiClient.get(`/assets/${symbol}`);
            return data;
        },
        enabled: !!symbol,
        refetchInterval: 10000, // Refetch every 10 seconds
    });
};
