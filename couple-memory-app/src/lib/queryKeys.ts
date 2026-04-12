export const queryKeys = {
  memories: (coupleSpaceId: string) => ["memories", coupleSpaceId] as const,
  memory: (id: string) => ["memory", id] as const,
};
