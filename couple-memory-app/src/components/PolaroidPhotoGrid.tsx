import React from "react";
import { Image, StyleSheet, Text, View } from "react-native";

import { theme } from "@/constants/theme";

type Props = {
  photos: string[];
  emptyLabel?: string;
  compact?: boolean;
};

export function PolaroidPhotoGrid({
  photos,
  emptyLabel = "No photos yet",
  compact = false,
}: Props) {
  if (!photos.length) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyLabel}>{emptyLabel}</Text>
      </View>
    );
  }

  return (
    <View style={[styles.grid, compact && styles.compactGrid]}>
      {photos.slice(0, compact ? 3 : 6).map((photo, index) => (
        <View
          key={`${photo}-${index}`}
          style={[
            styles.frame,
            index % 2 === 0 ? styles.rotateLeft : styles.rotateRight,
            compact && styles.compactFrame,
          ]}
        >
          <Image source={{ uri: photo }} style={styles.photo} />
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: theme.spacing.md,
  },
  compactGrid: {
    gap: theme.spacing.sm,
  },
  frame: {
    width: 108,
    height: 132,
    borderRadius: 18,
    backgroundColor: theme.colors.white,
    padding: 8,
    ...theme.shadows.soft,
  },
  compactFrame: {
    width: 88,
    height: 108,
  },
  rotateLeft: {
    transform: [{ rotate: "-3deg" }],
  },
  rotateRight: {
    transform: [{ rotate: "3deg" }],
  },
  photo: {
    width: "100%",
    height: "100%",
    borderRadius: 14,
    backgroundColor: theme.colors.backgroundSecondary,
  },
  empty: {
    borderRadius: theme.radius.lg,
    backgroundColor: "rgba(255,255,255,0.68)",
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
  },
  emptyLabel: {
    color: theme.colors.textSecondary,
    lineHeight: 20,
  },
});
