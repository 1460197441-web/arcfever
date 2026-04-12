import { router } from "expo-router";
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import { isSupabaseConfigured } from "@/lib/env";
import { getInitialSession, onAuthStateChange, signInWithEmail, signOutCurrentUser } from "@/services/auth";
import { createCoupleSpace, getMembershipForUser, joinCoupleSpace } from "@/services/invites";
import type { AppUser, CoupleMember, CoupleSpace } from "@/types/domain";

type AuthContextValue = {
  initialized: boolean;
  loading: boolean;
  user: AppUser | null;
  coupleSpace: CoupleSpace | null;
  coupleMember: CoupleMember | null;
  memberCount: number;
  isConfigured: boolean;
  signIn: (email: string, verificationCode?: string) => Promise<string>;
  signOut: () => Promise<void>;
  refreshMembership: () => Promise<void>;
  createSpace: (name: string) => Promise<void>;
  joinByInvite: (inviteCode: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: React.PropsWithChildren) {
  const [initialized, setInitialized] = useState(false);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<AppUser | null>(null);
  const [coupleSpace, setCoupleSpace] = useState<CoupleSpace | null>(null);
  const [coupleMember, setCoupleMember] = useState<CoupleMember | null>(null);
  const [memberCount, setMemberCount] = useState(0);

  async function refreshMembershipInternal(nextUser = user) {
    if (!nextUser) {
      setCoupleSpace(null);
      setCoupleMember(null);
      setMemberCount(0);
      return;
    }

    const membership = await getMembershipForUser(nextUser.id);
    setCoupleSpace(membership.space);
    setCoupleMember(membership.member);
    setMemberCount(membership.memberCount);
  }

  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      try {
        const session = await getInitialSession();
        if (!mounted) {
          return;
        }

        setUser(session.user);
        if (session.user) {
          await refreshMembershipInternal(session.user);
        }
      } finally {
        if (mounted) {
          setInitialized(true);
        }
      }
    }

    bootstrap();

    const subscription = onAuthStateChange(async ({ user: nextUser }) => {
      setUser(nextUser);
      if (nextUser) {
        await refreshMembershipInternal(nextUser);
      } else {
        setCoupleSpace(null);
        setCoupleMember(null);
        setMemberCount(0);
      }
      setInitialized(true);
    });

    return () => {
      mounted = false;
      subscription.data.subscription.unsubscribe();
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      initialized,
      loading,
      user,
      coupleSpace,
      coupleMember,
      memberCount,
      isConfigured: isSupabaseConfigured,
      async signIn(email: string, verificationCode?: string) {
        setLoading(true);
        try {
          const result = await signInWithEmail(email.trim(), verificationCode);
          if (result.user) {
            setUser(result.user);
            await refreshMembershipInternal(result.user);
          }
          return result.message;
        } finally {
          setLoading(false);
        }
      },
      async signOut() {
        setLoading(true);
        try {
          await signOutCurrentUser();
          setUser(null);
          setCoupleSpace(null);
          setCoupleMember(null);
          setMemberCount(0);
          router.replace("/(auth)/login");
        } finally {
          setLoading(false);
        }
      },
      async refreshMembership() {
        await refreshMembershipInternal();
      },
      async createSpace(name: string) {
        if (!user) {
          throw new Error("Please sign in first.");
        }

        setLoading(true);
        try {
          await createCoupleSpace(user.id, name.trim());
          await refreshMembershipInternal(user);
        } finally {
          setLoading(false);
        }
      },
      async joinByInvite(inviteCode: string) {
        if (!user) {
          throw new Error("Please sign in first.");
        }

        setLoading(true);
        try {
          await joinCoupleSpace(user.id, inviteCode);
          await refreshMembershipInternal(user);
        } finally {
          setLoading(false);
        }
      },
    }),
    [initialized, loading, user, coupleSpace, coupleMember, memberCount],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthStore() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuthStore must be used within AuthProvider");
  }

  return context;
}
