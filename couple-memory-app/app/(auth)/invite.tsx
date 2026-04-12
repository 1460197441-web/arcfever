import { Redirect, router } from "expo-router";
import React, { useState } from "react";
import { Alert, StyleSheet, Text, View } from "react-native";

import { CoupleHeader } from "@/components/CoupleHeader";
import { FormField } from "@/components/FormField";
import { GradientButton } from "@/components/GradientButton";
import { Screen } from "@/components/Screen";
import { SoftCard } from "@/components/SoftCard";
import { theme } from "@/constants/theme";
import { useAuth } from "@/hooks/useAuth";

export default function InviteScreen() {
  const [spaceName, setSpaceName] = useState("Our Love Bubble");
  const [inviteCode, setInviteCode] = useState("");
  const { user, coupleSpace, memberCount, createSpace, joinByInvite, loading } = useAuth();

  if (!user) {
    return <Redirect href="/(auth)/login" />;
  }

  async function handleCreateSpace() {
    try {
      await createSpace(spaceName || "Our Love Bubble");
      Alert.alert(
        "Space created",
        "Send the invite code to your partner so both of you can enter the same private space.",
      );
    } catch (error) {
      Alert.alert("Create failed", error instanceof Error ? error.message : "Please try again.");
    }
  }

  async function handleJoin() {
    if (!inviteCode.trim()) {
      Alert.alert("Enter invite code", "Please enter the invite code first.");
      return;
    }

    try {
      await joinByInvite(inviteCode);
      Alert.alert("Connected", "You are now in the same couple space and can start saving memories together.", [
        { text: "Go to Feed", onPress: () => router.replace("/(tabs)/feed") },
      ]);
    } catch (error) {
      Alert.alert("Join failed", error instanceof Error ? error.message : "Please try again.");
    }
  }

  return (
    <Screen>
      <CoupleHeader
        mini
        status="For just two people"
        subtitle="Link both accounts into the same dreamy little space so your map, calendar, and feed all stay shared."
        title="Create your private couple room"
      />

      {coupleSpace ? (
        <SoftCard style={styles.spaceCard}>
          <Text style={styles.spaceLabel}>Current space</Text>
          <Text style={styles.spaceName}>{coupleSpace.name}</Text>
          <Text style={styles.codeLabel}>Invite code</Text>
          <Text style={styles.code}>{coupleSpace.invite_code}</Text>
          <Text style={styles.memberCount}>Members {memberCount}/2</Text>
          <GradientButton onPress={() => router.replace("/(tabs)/feed")} title="Enter Feed" />
        </SoftCard>
      ) : (
        <>
          <SoftCard style={styles.card}>
            <Text style={styles.cardTitle}>1. Create your couple space</Text>
            <FormField
              label="Space name"
              onChangeText={setSpaceName}
              placeholder="For example: Our Love Bubble"
              value={spaceName}
            />
            <GradientButton loading={loading} onPress={handleCreateSpace} title="Create space and generate invite code" />
          </SoftCard>

          <View style={styles.divider}>
            <Text style={styles.dividerText}>or</Text>
          </View>

          <SoftCard style={styles.card}>
            <Text style={styles.cardTitle}>2. Enter the invite code from your partner</Text>
            <FormField
              autoCapitalize="characters"
              label="Invite code"
              onChangeText={setInviteCode}
              placeholder="For example: HEARTMAP"
              value={inviteCode}
            />
            <GradientButton loading={loading} onPress={handleJoin} title="Join couple space" variant="secondary" />
          </SoftCard>
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: theme.spacing.md,
  },
  cardTitle: {
    color: theme.colors.text,
    fontSize: 18,
    fontWeight: "800",
  },
  divider: {
    alignItems: "center",
  },
  dividerText: {
    color: theme.colors.textMuted,
    fontWeight: "700",
  },
  spaceCard: {
    gap: theme.spacing.md,
  },
  spaceLabel: {
    color: theme.colors.textMuted,
    fontWeight: "700",
  },
  spaceName: {
    color: theme.colors.text,
    fontSize: 24,
    fontWeight: "900",
  },
  codeLabel: {
    color: theme.colors.textMuted,
    fontWeight: "700",
  },
  code: {
    color: theme.colors.primaryDark,
    fontSize: 32,
    letterSpacing: 3,
    fontWeight: "900",
  },
  memberCount: {
    color: theme.colors.textMuted,
  },
});
