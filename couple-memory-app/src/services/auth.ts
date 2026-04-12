import AsyncStorage from "@react-native-async-storage/async-storage";
import type { Session, User } from "@supabase/supabase-js";
import * as Linking from "expo-linking";

import { env, isSupabaseConfigured } from "@/lib/env";
import { supabase } from "@/lib/supabase";
import type { AppUser } from "@/types/domain";

const DEV_AUTH_STORAGE_KEY = "couple-memory-dev-auth";

type DevAuthSession = {
  user: AppUser;
};

function mapSupabaseUser(user: User): AppUser {
  return {
    id: user.id,
    email: user.email ?? "",
    displayName:
      (typeof user.user_metadata?.display_name === "string" && user.user_metadata.display_name) ||
      null,
  };
}

function createDevUser(email: string): AppUser {
  return {
    id: `dev-${email.toLowerCase()}`,
    email,
    displayName: email.split("@")[0],
  };
}

export function isDevelopmentUserId(userId?: string | null) {
  return Boolean(userId?.startsWith("dev-"));
}

async function saveDevSession(user: AppUser) {
  const payload: DevAuthSession = { user };
  await AsyncStorage.setItem(DEV_AUTH_STORAGE_KEY, JSON.stringify(payload));
}

async function readDevSession() {
  const raw = await AsyncStorage.getItem(DEV_AUTH_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as DevAuthSession;
    return parsed.user ?? null;
  } catch {
    return null;
  }
}

async function clearDevSession() {
  await AsyncStorage.removeItem(DEV_AUTH_STORAGE_KEY);
}

export async function signInWithEmail(email: string, verificationCode?: string) {
  const normalizedEmail = email.trim().toLowerCase();

  if (verificationCode?.trim()) {
    if (verificationCode.trim() !== env.devLoginCode) {
      throw new Error("Test verification code is incorrect.");
    }

    const user = createDevUser(normalizedEmail);
    await saveDevSession(user);

    return {
      user,
      message: "Signed in with the development test code.",
    };
  }

  if (!isSupabaseConfigured || !supabase) {
    throw new Error("Supabase is not configured. Use the development test code to sign in locally.");
  }

  const { error } = await supabase.auth.signInWithOtp({
    email: normalizedEmail,
    options: {
      emailRedirectTo: Linking.createURL("/"),
    },
  });

  if (error) {
    throw error;
  }

  return {
    user: null,
    message: "A sign-in link was sent to your email. Or use the development test code for direct sign-in.",
  };
}

export async function signOutCurrentUser() {
  await clearDevSession();

  if (!isSupabaseConfigured || !supabase) {
    return;
  }

  const { error } = await supabase.auth.signOut();

  if (error) {
    throw error;
  }
}

export async function getInitialSession() {
  const devUser = await readDevSession();
  if (devUser) {
    return {
      session: null,
      user: devUser,
    };
  }

  if (!isSupabaseConfigured || !supabase) {
    return {
      session: null,
      user: null,
    };
  }

  const { data, error } = await supabase.auth.getSession();

  if (error) {
    throw error;
  }

  return {
    session: data.session,
    user: data.session?.user ? mapSupabaseUser(data.session.user) : null,
  };
}

export function onAuthStateChange(
  callback: (payload: { session: Session | null; user: AppUser | null }) => void,
) {
  if (!isSupabaseConfigured || !supabase) {
    return {
      data: {
        subscription: {
          unsubscribe() {},
        },
      },
    };
  }

  return supabase.auth.onAuthStateChange((_event, session) => {
    callback({
      session,
      user: session?.user ? mapSupabaseUser(session.user) : null,
    });
  });
}
