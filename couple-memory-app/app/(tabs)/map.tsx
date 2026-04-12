import { useQueryClient } from "@tanstack/react-query";
import { router } from "expo-router";
import React from "react";
import { ActivityIndicator, Platform, Pressable, StyleSheet, Text, View } from "react-native";

import { CoupleHeader } from "@/components/CoupleHeader";
import { GradientButton } from "@/components/GradientButton";
import { MemoryBubbleMarker } from "@/components/MemoryBubbleMarker";
import { Screen } from "@/components/Screen";
import { SoftCard } from "@/components/SoftCard";
import { theme } from "@/constants/theme";
import { useAuth } from "@/hooks/useAuth";
import { useMemories } from "@/hooks/useMemories";
import { queryKeys } from "@/lib/queryKeys";
import { getInitialMapCenter } from "@/services/places";
import { getRegionFromMemories, normalizePoints } from "@/utils/map";

export default function MapScreen() {
  const queryClient = useQueryClient();
  const { coupleSpace, signOut } = useAuth();
  const { data: memories, isLoading, refetch } = useMemories(coupleSpace?.id);

  if (!coupleSpace) {
    return null;
  }

  const coupleSpaceId = coupleSpace.id;
  const center = getInitialMapCenter();
  const items = memories ?? [];
  const region = getRegionFromMemories(items, center);
  const plottedItems = normalizePoints(items);

  async function handleRefresh() {
    await refetch();
    await queryClient.invalidateQueries({ queryKey: queryKeys.memories(coupleSpaceId) });
  }

  return (
    <Screen>
      <CoupleHeader
        mini
        status="回忆气泡"
        subtitle="你们一起走过的地方，都会在这里变成一颗会发光的小泡泡"
        title={coupleSpace.name}
      />

      <SoftCard style={styles.switchCard}>
        <View style={styles.switchRow}>
          <View style={[styles.switchPill, styles.switchPillActive]}>
            <Text style={styles.switchTextActive}>Map</Text>
          </View>
          <View style={styles.switchPill}>
            <Text style={styles.switchText}>Globe</Text>
          </View>
        </View>
      </SoftCard>

      {Platform.OS === "web" ? (
        <SoftCard style={styles.webMap}>
          <Text style={styles.mapLabel}>Dream map</Text>
          <Text style={styles.mapHint}>先用 2D 回忆地图承接氛围，后面再把 Globe 做成更梦幻的地球。</Text>
          <View style={styles.mapPlane}>
            {plottedItems.map((memory) => (
              <Pressable
                key={memory.id}
                onPress={() => router.push(`/memory/${memory.id}`)}
                style={[
                  styles.dotWrap,
                  {
                    left: `${memory.x}%`,
                    top: `${memory.y}%`,
                  },
                ]}
              >
                <MemoryBubbleMarker date={memory.date} title={memory.title} />
              </Pressable>
            ))}
          </View>
        </SoftCard>
      ) : (
        <NativeMap memories={items} region={region} onSelect={(id) => router.push(`/memory/${id}`)} />
      )}

      <View style={styles.toolbar}>
        <GradientButton onPress={handleRefresh} title="Refresh" variant="secondary" />
        <GradientButton onPress={() => router.push("/(tabs)/new-memory")} title="Add memory" />
        <GradientButton onPress={signOut} title="Sign out" variant="ghost" />
      </View>

      {isLoading ? (
        <ActivityIndicator color={theme.colors.primary} />
      ) : items.length ? (
        <SoftCard style={styles.sheet}>
          <Text style={styles.sectionTitle}>回忆泡泡</Text>
          {items.slice(0, 3).map((memory) => (
            <Pressable key={memory.id} onPress={() => router.push(`/memory/${memory.id}`)} style={styles.sheetItem}>
              <View style={styles.sheetDot} />
              <View style={styles.sheetContent}>
                <Text style={styles.sheetTitle}>{memory.place_name}</Text>
                <Text style={styles.sheetMeta}>
                  {memory.date} · {memory.title}
                </Text>
                <Text numberOfLines={1} style={styles.sheetNote}>
                  {memory.note || "这颗回忆泡泡还没写上小句子。"}
                </Text>
              </View>
            </Pressable>
          ))}
        </SoftCard>
      ) : (
        <SoftCard style={styles.empty}>
          <Text style={styles.emptyTitle}>No memory points yet</Text>
          <Text style={styles.emptyText}>Create your first memory bubble and let the map start glowing.</Text>
        </SoftCard>
      )}
    </Screen>
  );
}

function NativeMap({
  memories,
  region,
  onSelect,
}: {
  memories: Array<{ id: string; title: string; lat: number; lng: number; date: string }>;
  region: {
    latitude: number;
    longitude: number;
    latitudeDelta: number;
    longitudeDelta: number;
  };
  onSelect: (id: string) => void;
}) {
  const dynamicRequire = globalThis.Function("return require")() as NodeRequire;
  const mapsModule = dynamicRequire("react-native-maps");
  const MapView = mapsModule.default;
  const Marker = mapsModule.Marker;

  return (
    <View style={styles.nativeMapWrapper}>
      <MapView initialRegion={region} style={styles.nativeMap}>
        {memories.map((memory) => (
          <Marker
            coordinate={{ latitude: memory.lat, longitude: memory.lng }}
            key={memory.id}
            onPress={() => onSelect(memory.id)}
            title={memory.title}
          />
        ))}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  switchCard: {
    paddingVertical: 12,
  },
  switchRow: {
    flexDirection: "row",
    gap: 10,
    alignSelf: "flex-start",
  },
  switchPill: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: theme.radius.pill,
    backgroundColor: "rgba(255,255,255,0.6)",
  },
  switchPillActive: {
    backgroundColor: "#FFE3F1",
  },
  switchText: {
    color: theme.colors.textMuted,
    fontWeight: "700",
  },
  switchTextActive: {
    color: theme.colors.primary,
    fontWeight: "800",
  },
  webMap: {
    gap: theme.spacing.sm,
  },
  mapLabel: {
    color: theme.colors.text,
    fontSize: 16,
    fontWeight: "800",
  },
  mapHint: {
    color: theme.colors.textMuted,
    fontSize: 13,
    lineHeight: 18,
  },
  mapPlane: {
    height: 320,
    borderRadius: 28,
    backgroundColor: "rgba(255,240,247,0.85)",
    overflow: "hidden",
    position: "relative",
  },
  dotWrap: {
    position: "absolute",
    marginLeft: -20,
    marginTop: -20,
  },
  nativeMapWrapper: {
    borderRadius: theme.radius.lg,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  nativeMap: {
    width: "100%",
    height: 260,
  },
  toolbar: {
    flexDirection: "row",
    gap: theme.spacing.sm,
    flexWrap: "wrap",
  },
  sectionTitle: {
    color: theme.colors.text,
    fontSize: 18,
    fontWeight: "800",
  },
  sheet: {
    gap: theme.spacing.md,
  },
  sheetItem: {
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
  },
  sheetDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: theme.colors.primary,
    marginTop: 6,
    ...theme.shadows.glow,
  },
  sheetContent: {
    flex: 1,
    gap: 4,
  },
  sheetTitle: {
    color: theme.colors.text,
    fontWeight: "800",
  },
  sheetMeta: {
    color: theme.colors.primary,
    fontSize: 12,
    fontWeight: "700",
  },
  sheetNote: {
    color: theme.colors.textMuted,
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
    lineHeight: 21,
  },
});
