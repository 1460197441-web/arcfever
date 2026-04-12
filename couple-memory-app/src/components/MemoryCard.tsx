import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { MoodChip } from "@/components/MoodChip";
import { SoftCard } from "@/components/SoftCard";
import { theme } from "@/constants/theme";
import type { Memory } from "@/types/domain";
import { formatDisplayDate } from "@/utils/date";

type Props = {
  memory: Memory;
  onPress: () => void;
};

export function MemoryCard({ memory, onPress }: Props) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [pressed && styles.pressed]}>
      <SoftCard style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.title}>{memory.title}</Text>
          <Text style={styles.date}>{formatDisplayDate(memory.date)}</Text>
        </View>
        <MoodChip icon="📍" label={memory.place_name} />
        <Text style={styles.note} numberOfLines={2}>
          {memory.note || "这一天还没补上小心情。"}
        </Text>
        <Text style={styles.meta}>
          {memory.photos.length} 张照片 · {memory.lat.toFixed(4)}, {memory.lng.toFixed(4)}
        </Text>
      </SoftCard>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: theme.spacing.sm,
  },
  pressed: {
    opacity: 0.92,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: theme.spacing.sm,
  },
  title: {
    flex: 1,
    color: theme.colors.text,
    fontSize: 17,
    fontWeight: "800",
  },
  date: {
    color: theme.colors.textMuted,
    fontSize: 12,
    fontWeight: "600",
  },
  note: {
    color: theme.colors.textMuted,
    lineHeight: 21,
  },
  meta: {
    color: theme.colors.textMuted,
    fontSize: 12,
  },
});
