import { useQueryClient } from "@tanstack/react-query";
import * as ImagePicker from "expo-image-picker";
import * as Location from "expo-location";
import { router } from "expo-router";
import React, { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { CoupleHeader } from "@/components/CoupleHeader";
import { FormField } from "@/components/FormField";
import { GradientButton } from "@/components/GradientButton";
import { PolaroidPhotoGrid } from "@/components/PolaroidPhotoGrid";
import { Screen } from "@/components/Screen";
import { SoftCard } from "@/components/SoftCard";
import { theme } from "@/constants/theme";
import { useAuth } from "@/hooks/useAuth";
import { queryKeys } from "@/lib/queryKeys";
import { createMemory } from "@/services/memories";
import { resolvePhotoUrls } from "@/services/storage";

export default function NewMemoryScreen() {
  const queryClient = useQueryClient();
  const { user, coupleSpace } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [placeName, setPlaceName] = useState("");
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [note, setNote] = useState("");
  const [photos, setPhotos] = useState<string[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);

  useEffect(() => {
    let active = true;

    async function loadPreviewUrls() {
      try {
        const nextUrls = await resolvePhotoUrls(photos);
        if (active) {
          setPreviewUrls(nextUrls);
        }
      } catch {
        if (active) {
          setPreviewUrls(photos);
        }
      }
    }

    loadPreviewUrls();

    return () => {
      active = false;
    };
  }, [photos]);

  async function handlePickPhotos() {
    const result = await ImagePicker.launchImageLibraryAsync({
      allowsMultipleSelection: true,
      mediaTypes: ["images"],
      quality: 0.8,
      selectionLimit: 5,
    });

    if (result.canceled) {
      return;
    }

    setPhotos(result.assets.map((asset) => asset.uri));
  }

  async function handleUseLocation() {
    const permission = await Location.requestForegroundPermissionsAsync();
    if (permission.status !== "granted") {
      setErrorMessage("Location denied. Please fill in latitude and longitude manually.");
      return;
    }

    const current = await Location.getCurrentPositionAsync({});
    setLat(current.coords.latitude.toFixed(6));
    setLng(current.coords.longitude.toFixed(6));
  }

  async function handleSubmit() {
    if (!user || !coupleSpace) {
      setErrorMessage("Please log in and join a couple space first.");
      setFeedback(null);
      return;
    }

    if (!title || !date || !placeName || !lat || !lng) {
      setErrorMessage("Please fill in all required fields.");
      setFeedback(null);
      return;
    }

    setSubmitting(true);
    try {
      setErrorMessage(null);
      await createMemory({
        title,
        date,
        place_name: placeName,
        lat: Number(lat),
        lng: Number(lng),
        note,
        photos,
        author_id: user.id,
        couple_space_id: coupleSpace.id,
      });

      await queryClient.invalidateQueries({ queryKey: queryKeys.memories(coupleSpace.id) });
      setFeedback("Saved. Redirecting back to the map...");
      router.replace("/(tabs)/map");
    } catch (error) {
      setFeedback(null);
      setErrorMessage(error instanceof Error ? error.message : "Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Screen>
      <CoupleHeader
        mini
        status="记录当下"
        subtitle="把约会的地点、心情和照片装进一颗新的粉紫糖果里"
        title="新增回忆"
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
        <GradientButton onPress={handleUseLocation} title="Use current location" variant="secondary" />
        <FormField
          label="Note"
          multiline
          onChangeText={setNote}
          placeholder="Write down what happened, what you talked about, or how it felt."
          value={note}
        />
        <GradientButton onPress={handlePickPhotos} title="Pick photos" variant="secondary" />

        {previewUrls.length ? (
          <PolaroidPhotoGrid compact photos={previewUrls} />
        ) : (
          <Text style={styles.photoHint}>No photos selected yet. In Supabase mode, these images will upload to Storage.</Text>
        )}

        <GradientButton loading={submitting} onPress={handleSubmit} title="Save memory" />
        {feedback ? <Text style={styles.successText}>{feedback}</Text> : null}
        {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
      </SoftCard>
    </Screen>
  );
}

const styles = StyleSheet.create({
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
  photoHint: {
    color: theme.colors.textMuted,
    lineHeight: 20,
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
