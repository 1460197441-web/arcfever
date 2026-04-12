import { useQueryClient } from "@tanstack/react-query";
import { Redirect, router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useState } from "react";
import { ActivityIndicator, Alert, StyleSheet, Text, View } from "react-native";

import { GradientButton } from "@/components/GradientButton";
import { MoodChip } from "@/components/MoodChip";
import { PolaroidPhotoGrid } from "@/components/PolaroidPhotoGrid";
import { Screen } from "@/components/Screen";
import { SoftCard } from "@/components/SoftCard";
import { theme } from "@/constants/theme";
import { useAuth } from "@/hooks/useAuth";
import { useMemory } from "@/hooks/useMemories";
import { queryKeys } from "@/lib/queryKeys";
import { deleteMemory } from "@/services/memories";
import { resolvePhotoUrls } from "@/services/storage";
import { formatDisplayDate } from "@/utils/date";

export default function MemoryDetailScreen() {
  const queryClient = useQueryClient();
  const params = useLocalSearchParams<{ id: string }>();
  const { user } = useAuth();
  const { data: memory, isLoading } = useMemory(params.id);
  const [photoUrls, setPhotoUrls] = useState<string[]>([]);
  const [loadingPhotos, setLoadingPhotos] = useState(false);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadPhotos() {
      if (!memory?.photos.length) {
        setPhotoUrls([]);
        setPhotoError(null);
        return;
      }

      setLoadingPhotos(true);
      setPhotoError(null);

      try {
        const nextUrls = await resolvePhotoUrls(memory.photos);
        if (active) {
          setPhotoUrls(nextUrls);
        }
      } catch (error) {
        if (active) {
          setPhotoUrls([]);
          setPhotoError(error instanceof Error ? error.message : "Unable to load photos.");
        }
      } finally {
        if (active) {
          setLoadingPhotos(false);
        }
      }
    }

    loadPhotos();

    return () => {
      active = false;
    };
  }, [memory?.photos]);

  if (!user) {
    return <Redirect href="/(auth)/login" />;
  }

  if (isLoading) {
    return (
      <Screen>
        <View style={styles.center}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </Screen>
    );
  }

  if (!memory) {
    return (
      <Screen>
        <SoftCard style={styles.empty}>
          <Text style={styles.emptyTitle}>Memory not found</Text>
          <Text style={styles.emptyText}>It may still be syncing, or it may have been removed.</Text>
        </SoftCard>
      </Screen>
    );
  }

  const currentMemory = memory;

  async function handleDelete() {
    setDeleting(true);
    try {
      const cleanup = await deleteMemory(currentMemory.id);
      await queryClient.invalidateQueries({ queryKey: queryKeys.memories(currentMemory.couple_space_id) });
      await queryClient.invalidateQueries({ queryKey: queryKeys.memory(currentMemory.id) });

      if (cleanup.failedStoragePaths.length) {
        Alert.alert(
          "Memory deleted",
          "The memory was removed, but some private files could not be cleaned up automatically.",
          [{ text: "Back to map", onPress: () => router.replace("/(tabs)/map") }],
        );
        return;
      }

      Alert.alert("Memory deleted", "The memory and its private photo references were removed.", [
        { text: "Back to map", onPress: () => router.replace("/(tabs)/map") },
      ]);
    } catch (error) {
      Alert.alert("Delete failed", error instanceof Error ? error.message : "Please try again.");
    } finally {
      setDeleting(false);
    }
  }

  function confirmDelete() {
    Alert.alert(
      "Delete memory",
      "This will remove the memory record and try to clean up all private photos from Storage.",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Delete", style: "destructive", onPress: () => void handleDelete() },
      ],
    );
  }

  return (
    <Screen>
      <View style={styles.hero}>
        <Text style={styles.title}>{memory.title}</Text>
        <Text style={styles.date}>{formatDisplayDate(memory.date)}</Text>
      </View>

      <SoftCard style={styles.card}>
        {loadingPhotos ? <ActivityIndicator color={theme.colors.primary} /> : <PolaroidPhotoGrid photos={photoUrls} />}
        {photoError ? <Text style={styles.errorText}>{photoError}</Text> : null}
      </SoftCard>

      <SoftCard style={styles.card}>
        <View style={styles.chipRow}>
          <MoodChip icon="📍" label={currentMemory.place_name} />
          <MoodChip icon="♡" label={currentMemory.author_id === user.id ? "你记录的" : "她记录的"} />
        </View>
        <Text style={styles.note}>{currentMemory.note || "No note yet for this memory."}</Text>
        <Text style={styles.meta}>
          Coords {currentMemory.lat.toFixed(6)}, {currentMemory.lng.toFixed(6)}
        </Text>
        <GradientButton onPress={() => router.push(`/memory/${currentMemory.id}/edit`)} title="Edit memory" variant="secondary" />
      </SoftCard>

      <SoftCard style={styles.card}>
        <Text style={styles.sectionLabel}>Danger zone</Text>
        <Text style={styles.meta}>Delete removes the memory entry first and then cleans up private Storage files.</Text>
        <GradientButton
          disabled={deleting}
          loading={deleting}
          onPress={confirmDelete}
          title="Delete this memory"
          variant="secondary"
        />
      </SoftCard>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: {
    gap: theme.spacing.xs,
  },
  title: {
    color: theme.colors.text,
    fontSize: 30,
    fontWeight: "900",
  },
  date: {
    color: theme.colors.textMuted,
  },
  card: {
    gap: theme.spacing.sm,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  sectionLabel: {
    color: theme.colors.textMuted,
    fontWeight: "700",
  },
  meta: {
    color: theme.colors.textMuted,
    lineHeight: 20,
  },
  note: {
    color: theme.colors.text,
    lineHeight: 24,
  },
  errorText: {
    color: theme.colors.danger,
    lineHeight: 20,
  },
  empty: {
    gap: theme.spacing.xs,
  },
  emptyTitle: {
    color: theme.colors.text,
    fontWeight: "800",
  },
  emptyText: {
    color: theme.colors.textMuted,
  },
  center: {
    alignItems: "center",
    justifyContent: "center",
    minHeight: 220,
  },
});
