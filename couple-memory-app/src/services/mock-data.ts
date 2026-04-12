import type {
  CoupleMember,
  CoupleSpace,
  CreateMemoryInput,
  Memory,
  UpdateMemoryFieldsInput,
} from "@/types/domain";

const now = new Date().toISOString();

export const mockSpaces: CoupleSpace[] = [];
export const mockMembers: CoupleMember[] = [];
export const mockMemories: Memory[] = [
  {
    id: "memory-demo-1",
    title: "First dessert date",
    date: "2026-03-14",
    place_name: "Jing'an",
    lat: 31.2054,
    lng: 121.4372,
    note: "Coffee, dessert, and a long walk under the trees. It felt like the right first memory to keep.",
    photos: [],
    author_id: "demo-owner",
    couple_space_id: "demo-space",
    created_at: now,
    updated_at: now,
  },
];

mockSpaces.push({
  id: "demo-space",
  name: "Our little universe",
  invite_code: "HEARTMAP",
  owner_user_id: "demo-owner",
  max_members: 2,
  created_at: now,
});

mockMembers.push({
  id: "member-demo-owner",
  couple_space_id: "demo-space",
  user_id: "demo-owner",
  role: "owner",
  joined_at: now,
});

export function makeMockId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

export function isMockEntityId(value?: string | null) {
  return Boolean(
    value &&
      (value.startsWith("memory-") ||
        value.startsWith("space-") ||
        value.startsWith("member-") ||
        value.startsWith("dev-")),
  );
}

export function appendMockMemory(input: CreateMemoryInput): Memory {
  const memory: Memory = {
    id: makeMockId("memory"),
    ...input,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  mockMemories.unshift(memory);
  return memory;
}

export function removeMockMemory(memoryId: string) {
  const index = mockMemories.findIndex((item) => item.id === memoryId);
  if (index === -1) {
    return null;
  }

  const [removed] = mockMemories.splice(index, 1);
  return removed;
}

export function replaceMockMemoryPhotos(memoryId: string, photos: string[]) {
  const memory = mockMemories.find((item) => item.id === memoryId);
  if (!memory) {
    return null;
  }

  memory.photos = photos;
  memory.updated_at = new Date().toISOString();
  return memory;
}

export function updateMockMemory(memoryId: string, updates: UpdateMemoryFieldsInput) {
  const memory = mockMemories.find((item) => item.id === memoryId);
  if (!memory) {
    return null;
  }

  Object.assign(memory, updates, {
    updated_at: new Date().toISOString(),
  });

  return memory;
}
