import { isDevelopmentUserId } from "@/services/auth";
import { isSupabaseConfigured } from "@/lib/env";
import { supabase } from "@/lib/supabase";
import { makeMockId, mockMembers, mockSpaces } from "@/services/mock-data";
import type { CoupleMember, CoupleSpace } from "@/types/domain";

export async function getMembershipForUser(userId: string): Promise<{
  space: CoupleSpace | null;
  member: CoupleMember | null;
  memberCount: number;
}> {
  if (!isSupabaseConfigured || !supabase || isDevelopmentUserId(userId)) {
    const member = mockMembers.find((item) => item.user_id === userId) ?? null;
    const space = member ? mockSpaces.find((item) => item.id === member.couple_space_id) ?? null : null;
    const memberCount = member ? mockMembers.filter((item) => item.couple_space_id === member.couple_space_id).length : 0;

    return { space, member, memberCount };
  }

  const client = supabase as any;

  const { data: memberRow, error: memberError } = await client
    .from("couple_members")
    .select("*")
    .eq("user_id", userId)
    .maybeSingle();

  if (memberError) {
    throw memberError;
  }

  if (!memberRow) {
    return { space: null, member: null, memberCount: 0 };
  }

  const { data: spaceRow, error: spaceError } = await client
    .from("couple_spaces")
    .select("*")
    .eq("id", memberRow.couple_space_id)
    .single();

  if (spaceError) {
    throw spaceError;
  }

  const { count, error: countError } = await client
    .from("couple_members")
    .select("*", { count: "exact", head: true })
    .eq("couple_space_id", memberRow.couple_space_id);

  if (countError) {
    throw countError;
  }

  return {
    space: spaceRow,
    member: memberRow,
    memberCount: count ?? 0,
  };
}

export async function createCoupleSpace(userId: string, name: string): Promise<CoupleSpace> {
  if (!isSupabaseConfigured || !supabase || isDevelopmentUserId(userId)) {
    const existing = mockMembers.find((item) => item.user_id === userId);
    if (existing) {
      const space = mockSpaces.find((item) => item.id === existing.couple_space_id);
      if (space) {
        return space;
      }
    }

    const inviteCode = `LOVE${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
    const space: CoupleSpace = {
      id: makeMockId("space"),
      name,
      invite_code: inviteCode,
      owner_user_id: userId,
      max_members: 2,
      created_at: new Date().toISOString(),
    };
    const member: CoupleMember = {
      id: makeMockId("member"),
      couple_space_id: space.id,
      user_id: userId,
      role: "owner",
      joined_at: new Date().toISOString(),
    };

    mockSpaces.push(space);
    mockMembers.push(member);
    return space;
  }

  const client = supabase as any;

  const { data, error } = await client.rpc("create_couple_space", {
    p_name: name,
  });

  if (error) {
    throw error;
  }

  const { data: spaceRow, error: spaceError } = await client
    .from("couple_spaces")
    .select("*")
    .eq("id", data)
    .single();

  if (spaceError) {
    throw spaceError;
  }

  return spaceRow;
}

export async function joinCoupleSpace(userId: string, inviteCode: string): Promise<CoupleSpace> {
  if (!isSupabaseConfigured || !supabase || isDevelopmentUserId(userId)) {
    const normalized = inviteCode.trim().toUpperCase();
    const existingMembership = mockMembers.find((item) => item.user_id === userId);
    if (existingMembership) {
      const existingSpace = mockSpaces.find((item) => item.id === existingMembership.couple_space_id);
      if (existingSpace) {
        return existingSpace;
      }
    }

    const space = mockSpaces.find((item) => item.invite_code === normalized);
    if (!space) {
      throw new Error("Invite code not found. Please double-check and try again.");
    }

    const currentMembers = mockMembers.filter((item) => item.couple_space_id === space.id);
    if (currentMembers.length >= 2) {
      throw new Error("This couple space is already full.");
    }

    mockMembers.push({
      id: makeMockId("member"),
      couple_space_id: space.id,
      user_id: userId,
      role: "partner",
      joined_at: new Date().toISOString(),
    });
    return space;
  }

  const client = supabase as any;

  const { data, error } = await client.rpc("join_couple_space", {
    p_invite_code: inviteCode.trim().toUpperCase(),
  });

  if (error) {
    throw error;
  }

  const { data: spaceRow, error: spaceError } = await client
    .from("couple_spaces")
    .select("*")
    .eq("id", data)
    .single();

  if (spaceError) {
    throw spaceError;
  }

  return spaceRow;
}
