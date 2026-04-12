import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { theme } from "@/constants/theme";

type Props = {
  label: string;
  icon?: string;
};

export function MoodChip({ label, icon = "♡" }: Props) {
  return (
    <View style={styles.chip}>
      <Text style={styles.icon}>{icon}</Text>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: theme.spacing.xxs,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: theme.radius.pill,
    backgroundColor: "rgba(255,240,248,0.88)",
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  icon: {
    color: theme.colors.accent,
    fontSize: 12,
  },
  label: {
    color: theme.colors.textPrimary,
    fontSize: 12,
    fontWeight: "700",
  },
});
