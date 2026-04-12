import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/lib/queryKeys";
import { getMemoryById, listMemories } from "@/services/memories";

export function useMemories(coupleSpaceId?: string | null) {
  return useQuery({
    queryKey: queryKeys.memories(coupleSpaceId ?? "missing"),
    queryFn: () => listMemories(coupleSpaceId ?? ""),
    enabled: Boolean(coupleSpaceId),
  });
}

export function useMemory(memoryId?: string | null) {
  return useQuery({
    queryKey: memoryId ? queryKeys.memory(memoryId) : ["memory", "missing"],
    queryFn: () => getMemoryById(memoryId ?? ""),
    enabled: Boolean(memoryId),
  });
}
