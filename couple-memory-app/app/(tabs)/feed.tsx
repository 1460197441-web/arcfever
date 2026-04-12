import { router } from "expo-router";
import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

import { CoupleHeader } from "@/components/CoupleHeader";
import { MoodChip } from "@/components/MoodChip";
import { PolaroidPhotoGrid } from "@/components/PolaroidPhotoGrid";
import { Screen } from "@/components/Screen";
import { SoftCard } from "@/components/SoftCard";
import { theme } from "@/constants/theme";
import { useAuth } from "@/hooks/useAuth";
import { useMemories } from "@/hooks/useMemories";
import { formatDisplayDate } from "@/utils/date";

export default function FeedScreen() {
  const { coupleSpace, user } = useAuth();
  const { data: memories } = useMemories(coupleSpace?.id);
  const items = (memories ?? []).slice().sort((a, b) => (a.date < b.date ? 1 : -1));

  return (
    <Screen>
      <CoupleHeader
        dayCount={428}
        status="Pink bubbles only"
        subtitle="A tiny private timeline for just the two of you, where every date night, walk, and sweet little thought gets saved."
        title="Our love universe"
      />

      <SoftCard style={styles.composerCard}>
        <Text style={styles.inputTitle}>What do you want to remember today?</Text>
        <Pressable onPress={() => router.push("/(tabs)/new-memory")} style={styles.fakeInput}>
          <Text style={styles.fakeInputIcon}>✦</Text>
          <Text style={styles.fakeInputText}>Post a tiny update that only belongs to the two of you...</Text>
        </Pressable>
      </SoftCard>

      {items.length ? (
        items.map((memory, index) => {
          const isMe = memory.author_id === user?.id;
          const moodLabel = index % 2 === 0 ? "Soft and sweet" : "Want a cuddle";
          const moodIcon = index % 2 === 0 ? "♡" : "✦";
          const authorLabel = isMe ? "You" : "Her";
          const note = memory.note || `${memory.title} was one more lovely page in your shared diary.`;

          return (
            <Pressable key={memory.id} onPress={() => router.push(`/memory/${memory.id}`)}>
              <SoftCard style={styles.postCard}>
                <View style={styles.row}>
                  <Image
                    source={{ uri: isMe ? "https://i.pravatar.cc/100?img=32" : "https://i.pravatar.cc/100?img=47" }}
                    style={styles.postAvatar}
                  />
                  <View style={styles.flex}>
                    <Text style={styles.name}>{authorLabel}</Text>
                    <Text style={styles.time}>{formatDisplayDate(memory.date)}</Text>
                  </View>
                  <MoodChip icon={moodIcon} label={moodLabel} />
                </View>

                <Text style={styles.postText}>{note}</Text>
                <PolaroidPhotoGrid compact photos={memory.photos} />
                <View style={styles.metaRow}>
                  <Text style={styles.place}>📍 {memory.place_name}</Text>
                  <Text style={styles.metaHint}>{memory.title}</Text>
                </View>

                <View style={styles.actions}>
                  <Pressable style={styles.actionBtn}>
                    <Text style={styles.actionText}>Heart flutter</Text>
                  </Pressable>
                  <Pressable style={styles.actionBtn}>
                    <Text style={styles.actionText}>Leave a note</Text>
                  </Pressable>
                </View>
              </SoftCard>
            </Pressable>
          );
        })
      ) : (
        <LinearGradient colors={[theme.colors.dreamGradientStart, theme.colors.dreamGradientEnd]} style={styles.emptyHero}>
          <Text style={styles.emptyTitle}>No posts yet</Text>
          <Text style={styles.emptyText}>Save the first memory and let your private little universe start glowing.</Text>
        </LinearGradient>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  composerCard: {
    gap: theme.spacing.sm,
  },
  inputTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: theme.colors.text,
  },
  fakeInput: {
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.72)",
    padding: 14,
    flexDirection: "row",
    gap: 8,
    alignItems: "center",
  },
  fakeInputIcon: {
    color: theme.colors.primary,
    fontWeight: "900",
  },
  fakeInputText: {
    color: theme.colors.textMuted,
    flex: 1,
  },
  postCard: {
    gap: 12,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
  },
  flex: {
    flex: 1,
  },
  postAvatar: {
    width: 42,
    height: 42,
    borderRadius: 21,
    marginRight: 10,
    borderWidth: 2,
    borderColor: "rgba(255,255,255,0.8)",
  },
  name: {
    color: theme.colors.text,
    fontWeight: "700",
    fontSize: 15,
  },
  time: {
    color: theme.colors.textMuted,
    fontSize: 12,
    marginTop: 2,
  },
  postText: {
    color: theme.colors.text,
    fontSize: 15,
    lineHeight: 22,
  },
  metaRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
  },
  place: {
    color: theme.colors.textMuted,
    fontSize: 13,
    flex: 1,
  },
  metaHint: {
    color: theme.colors.primary,
    fontSize: 12,
    fontWeight: "700",
  },
  actions: {
    flexDirection: "row",
    gap: 10,
  },
  actionBtn: {
    flex: 1,
    backgroundColor: "#FFF0F7",
    paddingVertical: 12,
    borderRadius: theme.radius.pill,
    alignItems: "center",
  },
  actionText: {
    color: theme.colors.primary,
    fontWeight: "700",
  },
  emptyHero: {
    borderRadius: theme.radius.xl,
    padding: theme.spacing.xl,
    gap: theme.spacing.sm,
    ...theme.shadows.glow,
  },
  emptyTitle: {
    color: theme.colors.white,
    fontSize: 24,
    fontWeight: "900",
  },
  emptyText: {
    color: "rgba(255,255,255,0.9)",
    lineHeight: 22,
  },
});
