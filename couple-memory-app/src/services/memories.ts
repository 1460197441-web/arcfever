import { isDevelopmentUserId } from "@/services/auth";
import { isSupabaseConfigured } from "@/lib/env";
import { supabase } from "@/lib/supabase";
import {
  appendMockMemory,
  isMockEntityId,
  mockMemories,
  removeMockMemory,
  replaceMockMemoryPhotos,
  updateMockMemory,
} from "@/services/mock-data";
import {
  createMemoryId,
  deletePrivateMemoryFiles,
  uploadPrivateMemoryPhoto,
} from "@/services/storage";
import type { CreateMemoryInput, Memory, UpdateMemoryFieldsInput } from "@/types/domain";

export type MemoryCleanupResult = {
  failedStoragePaths: string[];
};

async function getCurrentUserId() {
  if (!supabase) {
    return null;
  }

  const { data, error } = await supabase.auth.getUser();
  if (error) {
    throw error;
  }

  return data.user?.id ?? null;
}

async function assertMemoryAccess(memoryId: string) {
  if (!supabase) {
    throw new Error("Supabase is not configured.");
  }

  const client = supabase as any;
  const userId = await getCurrentUserId();

  if (!userId) {
    throw new Error("Please log in first.");
  }

  const { data: memory, error: memoryError } = await client
    .from("memories")
    .select("*")
    .eq("id", memoryId)
    .maybeSingle();

  if (memoryError) {
    throw memoryError;
  }

  if (!memory) {
    throw new Error("Memory not found.");
  }

  const { data: member, error: memberError } = await client
    .from("couple_members")
    .select("id")
    .eq("couple_space_id", memory.couple_space_id)
    .eq("user_id", userId)
    .maybeSingle();

  if (memberError) {
    throw memberError;
  }

  if (!member) {
    throw new Error("You are not allowed to manage this memory.");
  }

  return {
    userId,
    memory: memory as Memory,
  };
}

async function replacePhotoRefs(memoryId: string, photoPaths: string[]) {
  if (!supabase) {
    throw new Error("Supabase is not configured.");
  }

  const client = supabase as any;
  const { data, error } = await client.rpc("replace_memory_photo_refs", {
    p_memory_id: memoryId,
    p_photo_paths: photoPaths,
  });

  if (error) {
    throw error;
  }

  return data as Memory;
}

export async function listMemories(coupleSpaceId: string): Promise<Memory[]> {
  if (!isSupabaseConfigured || !supabase || isMockEntityId(coupleSpaceId)) {
    return mockMemories
      .filter((item) => item.couple_space_id === coupleSpaceId)
      .sort((a, b) => b.date.localeCompare(a.date));
  }

  const client = supabase as any;

  const { data, error } = await client
    .from("memories")
    .select("*")
    .eq("couple_space_id", coupleSpaceId)
    .order("date", { ascending: false });

  if (error) {
    throw error;
  }

  return data;
}

export async function getMemoryById(memoryId: string): Promise<Memory | null> {
  if (!isSupabaseConfigured || !supabase || isMockEntityId(memoryId)) {
    return mockMemories.find((item) => item.id === memoryId) ?? null;
  }

  const client = supabase as any;
  const { data, error } = await client.from("memories").select("*").eq("id", memoryId).maybeSingle();

  if (error) {
    throw error;
  }

  return data;
}

export async function createMemory(input: CreateMemoryInput): Promise<Memory> {
  if (!isSupabaseConfigured || !supabase || isDevelopmentUserId(input.author_id)) {
    return appendMockMemory(input);
  }

  const client = supabase as any;
  const memoryId = createMemoryId();

  const photos = await Promise.all(
    input.photos.map((uri, index) =>
      uploadPrivateMemoryPhoto({
        sourceUri: uri,
        coupleSpaceId: input.couple_space_id,
        memoryId,
        index,
      }),
    ),
  );

  const { data, error } = await client
    .from("memories")
    .insert({
      id: memoryId,
      ...input,
      photos: [],
    })
    .select("*")
    .single();

  if (error) {
    await deletePrivateMemoryFiles(photos);
    throw error;
  }

  try {
    return await replacePhotoRefs(memoryId, photos);
  } catch (error) {
    await client.from("memories").delete().eq("id", memoryId);
    await deletePrivateMemoryFiles(photos);
    throw error;
  }
}

export async function replaceMemoryPhotos(memoryId: string, sourceUris: string[]) {
  if (!isSupabaseConfigured || !supabase || isMockEntityId(memoryId)) {
    const mockMemory = replaceMockMemoryPhotos(memoryId, sourceUris);
    if (!mockMemory) {
      throw new Error("Memory not found.");
    }

    return {
      memory: mockMemory,
      cleanup: {
        failedStoragePaths: [] as string[],
      },
    };
  }

  const { memory } = await assertMemoryAccess(memoryId);

  const uploadedPaths = await Promise.all(
    sourceUris.map((uri, index) =>
      uploadPrivateMemoryPhoto({
        sourceUri: uri,
        coupleSpaceId: memory.couple_space_id,
        memoryId,
        index,
      }),
    ),
  );

  try {
    const updatedMemory = await replacePhotoRefs(memoryId, uploadedPaths);
    const cleanup = await deletePrivateMemoryFiles(memory.photos);

    return {
      memory: updatedMemory,
      cleanup,
    };
  } catch (error) {
    await deletePrivateMemoryFiles(uploadedPaths);
    throw error;
  }
}

export async function updateMemoryFields(memoryId: string, updates: UpdateMemoryFieldsInput) {
  if (!isSupabaseConfigured || !supabase || isMockEntityId(memoryId)) {
    const updated = updateMockMemory(memoryId, updates);
    if (!updated) {
      throw new Error("Memory not found.");
    }

    return updated;
  }

  const { userId, memory } = await assertMemoryAccess(memoryId);
  if (memory.author_id !== userId) {
    throw new Error("Only the memory author can edit this memory.");
  }

  const client = supabase as any;
  const { data, error } = await client
    .from("memories")
    .update({
      ...updates,
    })
    .eq("id", memoryId)
    .eq("author_id", userId)
    .select("*")
    .single();

  if (error) {
    throw error;
  }

  return data as Memory;
}

export async function deleteMemory(memoryId: string): Promise<MemoryCleanupResult> {
  if (!isSupabaseConfigured || !supabase || isMockEntityId(memoryId)) {
    const removed = removeMockMemory(memoryId);
    if (!removed) {
      throw new Error("Memory not found.");
    }

    return {
      failedStoragePaths: [],
    };
  }

  await assertMemoryAccess(memoryId);
  const client = supabase as any;
  const { data, error } = await client.rpc("delete_memory_with_photo_refs", {
    p_memory_id: memoryId,
  });

  if (error) {
    throw error;
  }

  const cleanup = await deletePrivateMemoryFiles((data ?? []) as string[]);

  return {
    failedStoragePaths: cleanup.failedPaths,
  };
}
