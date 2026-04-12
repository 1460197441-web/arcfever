import { useQueryClient } from "@tanstack/react-query";
import { Redirect, router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useState } from "react";
import { ActivityIndicator, Alert, StyleSheet, Text, View } from "react-native";

import { CoupleHeader } from "@/components/CoupleHeader";
import { FormField } from "@/components/FormField";
import { GradientButton } from "@/components/GradientButton";
import { Screen } from "@/components/Screen";
import { SoftCard } from "@/components/SoftCard";
import { theme } from "@/constants/theme";
import { useAuth } from "@/hooks/useAuth";
import { useMemory } from "@/hooks/useMemories";
import { queryKeys } from "@/lib/queryKeys";
import { updateMemoryFields } from "@/services/memories";

export default function EditMemoryScreen() {
  const queryClient = useQueryClient();
  const params = useLocalSearchParams<{ id: string }>();
  const { user } = useAuth();
  const { data: memory, isLoading } = useMemory(params.id);
  const [submitting, setSubmitting] = useState(false);
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [placeName, setPlaceName] = useState("");
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [note, setNote] = useState("");

  useEffect(() => {
    if (!memory) {
      return;
    }

    setTitle(memory.title);
    setDate(memory.date);
    setPlaceName(memory.place_name);
    setLat(String(memory.lat));
    setLng(String(memory.lng));
    setNote(memory.note);
  }, [memory]);

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
        <SoftCard style={styles.card}>
          <Text style={styles.title}>Memory not found</Text>
          <Text style={styles.subtitle}>This memory may have been removed or is no longer accessible.</Text>
        </SoftCard>
      </Screen>
    );
  }

  const currentMemory = memory;

  async function handleSave() {
    if (!title || !date || !placeName || !lat || !lng) {
      Alert.alert("Incomplete form", "Please fill in all required fields.");
      return;
    }

    setSubmitting(true);
    try {
      const updated = await updateMemoryFields(currentMemory.id, {
        title,
        date,
        place_name: placeName,
        lat: Number(lat),
        lng: Number(lng),
        note,
      });

      await queryClient.invalidateQueries({ queryKey: queryKeys.memories(updated.couple_space_id) });
      await queryClient.invalidateQueries({ queryKey: queryKeys.memory(updated.id) });

      Alert.alert("Saved", "Memory details were updated.", [
        { text: "Back to detail", onPress: () => router.replace(`/memory/${updated.id}`) },
      ]);
    } catch (error) {
      Alert.alert("Save failed", error instanceof Error ? error.message : "Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Screen>
      <CoupleHeader
        mini
        status="轻轻修改"
        subtitle="把标题、地点和心情修得更像一本软糯糯的小日记"
        title="编辑回忆"
      />

      <SoftCard style={styles.card}>
        <FormField label="Title" onChangeText={setTitle} placeholder="Our first trip to the sea" value={title} />
        <FormField label="Date" onChangeText={setDate} placeholder="YYYY-MM-DD" value={date} />
        <FormField label="Place name" onChangeText={setPlaceName} placeholder="Dongji Island" value={placeName} />
        <View style={styles.row}>
          <View style={styles.flexField}>
            <FormField label="Latitude" onChangeText={setLat} placeholder="31.2304" value={lat} />
          </View>
          <View style={styles.flexField}>
            <FormField label="Longitude" onChangeText={setLng} placeholder="121.4737" value={lng} />
          </View>
        </View>
        <FormField
          label="Note"
          multiline
          onChangeText={setNote}
          placeholder="Write down what happened, what you talked about, or how it felt."
          value={note}
        />
        <GradientButton loading={submitting} onPress={handleSave} title="Save changes" />
      </SoftCard>
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: {
    alignItems: "center",
    justifyContent: "center",
    minHeight: 220,
  },
  title: {
    color: theme.colors.text,
    fontSize: 28,
    fontWeight: "900",
  },
  subtitle: {
    color: theme.colors.textMuted,
    lineHeight: 22,
  },
  card: {
    gap: theme.spacing.md,
  },
  row: {
    flexDirection: "row",
    gap: theme.spacing.sm,
  },
  flexField: {
    flex: 1,
  },
});
