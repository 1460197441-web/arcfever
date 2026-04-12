import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { MoodChip } from "@/components/MoodChip";
import { theme } from "@/constants/theme";

type Props = {
  title: string;
  subtitle: string;
  dayCount?: number;
  status?: string;
  mini?: boolean;
};

export function CoupleHeader({
  title,
  subtitle,
  dayCount = 428,
  status = "Pink bubble day",
  mini = false,
}: Props) {
  return (
    <LinearGradient
      colors={[theme.colors.dreamGradientStart, theme.colors.dreamGradientEnd]}
      end={{ x: 1, y: 1 }}
      start={{ x: 0, y: 0 }}
      style={[styles.wrap, mini && styles.miniWrap]}
    >
      <View style={styles.sparkles}>
        <Text style={styles.sparkle}>♡</Text>
        <Text style={styles.sparkle}>✦</Text>
        <Text style={styles.sparkle}>✦</Text>
      </View>

      <View style={styles.avatarRow}>
        <View style={styles.avatarPair}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>You</Text>
          </View>
          <View style={[styles.avatar, styles.avatarAccent]}>
            <Text style={styles.avatarText}>Her</Text>
          </View>
        </View>
        <MoodChip icon="♡" label={status} />
      </View>

      <Text style={[styles.title, mini && styles.miniTitle]}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
      <Text style={styles.metric}>Day {dayCount} together</Text>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderRadius: theme.radius.xl,
    padding: theme.spacing.xl,
    gap: theme.spacing.sm,
    ...theme.shadows.glow,
  },
  miniWrap: {
    padding: theme.spacing.lg,
  },
  sparkles: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  sparkle: {
    color: "rgba(255,255,255,0.92)",
    fontSize: 18,
  },
  avatarRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  avatarPair: {
    flexDirection: "row",
    alignItems: "center",
    marginLeft: 4,
  },
  avatar: {
    width: 42,
    height: 42,
    borderRadius: theme.radius.pill,
    backgroundColor: "rgba(255,255,255,0.82)",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "rgba(255,255,255,0.65)",
    marginLeft: -6,
  },
  avatarAccent: {
    backgroundColor: "rgba(255,240,248,0.95)",
  },
  avatarText: {
    color: theme.colors.textPrimary,
    fontWeight: "800",
    fontSize: 11,
  },
  title: {
    color: theme.colors.white,
    fontSize: 28,
    fontWeight: "900",
    lineHeight: 34,
  },
  miniTitle: {
    fontSize: 22,
    lineHeight: 28,
  },
  subtitle: {
    color: "rgba(255,255,255,0.92)",
    lineHeight: 22,
  },
  metric: {
    color: theme.colors.white,
    fontSize: 24,
    fontWeight: "900",
  },
});
