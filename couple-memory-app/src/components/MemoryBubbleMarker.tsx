import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { theme } from "@/constants/theme";

type Props = {
  title: string;
  date: string;
};

export function MemoryBubbleMarker({ title, date }: Props) {
  return (
    <View style={styles.wrap}>
      <View style={styles.dot} />
      <View style={styles.label}>
        <Text numberOfLines={1} style={styles.title}>
          {title}
        </Text>
        <Text style={styles.date}>{date}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    alignItems: "center",
    gap: theme.spacing.xs,
  },
  dot: {
    width: 24,
    height: 24,
    borderRadius: theme.radius.pill,
    backgroundColor: "rgba(255,111,174,0.92)",
    borderWidth: 4,
    borderColor: "rgba(255,255,255,0.85)",
    ...theme.shadows.glow,
  },
  label: {
    minWidth: 82,
    maxWidth: 120,
    borderRadius: 18,
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: "rgba(255,255,255,0.88)",
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  title: {
    color: theme.colors.textPrimary,
    fontWeight: "800",
    fontSize: 11,
  },
  date: {
    color: theme.colors.textSecondary,
    fontSize: 10,
    marginTop: 2,
  },
});
