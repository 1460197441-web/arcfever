import { router } from "expo-router";
import React, { useState } from "react";
import { StyleSheet, Text } from "react-native";

import { CoupleHeader } from "@/components/CoupleHeader";
import { FormField } from "@/components/FormField";
import { GradientButton } from "@/components/GradientButton";
import { Screen } from "@/components/Screen";
import { SoftCard } from "@/components/SoftCard";
import { theme } from "@/constants/theme";
import { useAuth } from "@/hooks/useAuth";
import { env } from "@/lib/env";

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [verificationCode, setVerificationCode] = useState(env.devLoginCode);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { signIn, loading, isConfigured } = useAuth();

  async function handleLogin(useEmailLink = false) {
    if (!email.trim()) {
      setErrorMessage("Please enter your email first.");
      setFeedback(null);
      return;
    }

    if (!useEmailLink && !verificationCode.trim()) {
      setErrorMessage("Use the default development test code: 246810.");
      setFeedback(null);
      return;
    }

    try {
      setErrorMessage(null);
      const message = await signIn(email, useEmailLink ? undefined : verificationCode);

      if (useEmailLink) {
        setFeedback(message);
        return;
      }

      setFeedback(message);
      router.replace("/(auth)/invite");
    } catch (error) {
      setFeedback(null);
      setErrorMessage(error instanceof Error ? error.message : "Please try again.");
    }
  }

  return (
    <Screen contentStyle={styles.content}>
      <CoupleHeader
        dayCount={428}
        status="Welcome back"
        subtitle="This is the private love space for you and her, with dreamy cards, shared memories, and pink little bubbles everywhere."
        title="Step into your little universe"
      />

      <SoftCard style={styles.notice}>
        <Text style={styles.noticeTitle}>Development sign-in</Text>
        <Text style={styles.noticeText}>Use any email plus the test code from `.env` or `app.json`. Default code: `246810`.</Text>
        {isConfigured ? (
          <Text style={styles.noticeText}>Real Supabase email-link sign-in is still available below when you want to test it.</Text>
        ) : (
          <Text style={styles.noticeText}>Supabase is not configured, so the test code path is the default login mode here.</Text>
        )}
      </SoftCard>

      <SoftCard style={styles.card}>
        <FormField
          autoCapitalize="none"
          autoComplete="email"
          keyboardType="email-address"
          label="Email"
          onChangeText={setEmail}
          placeholder="you@example.com"
          value={email}
        />
        <FormField label="Test code" onChangeText={setVerificationCode} placeholder="246810" value={verificationCode} />
        <GradientButton loading={loading} onPress={() => handleLogin(false)} title="Sign in with test code" />
        {isConfigured ? (
          <GradientButton
            loading={loading}
            onPress={() => handleLogin(true)}
            title="Send email sign-in link"
            variant="secondary"
          />
        ) : null}
        {feedback ? <Text style={styles.successText}>{feedback}</Text> : null}
        {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
      </SoftCard>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    flexGrow: 1,
    justifyContent: "center",
    gap: theme.spacing.xl,
  },
  notice: {
    gap: theme.spacing.xs,
  },
  noticeTitle: {
    color: theme.colors.text,
    fontWeight: "800",
  },
  noticeText: {
    color: theme.colors.textMuted,
    lineHeight: 20,
  },
  card: {
    gap: theme.spacing.md,
  },
  successText: {
    color: theme.colors.accent,
    lineHeight: 20,
  },
  errorText: {
    color: theme.colors.danger,
    lineHeight: 20,
  },
});
