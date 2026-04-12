import type { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";

import { theme } from "@/constants/theme";

const TAB_META: Record<string, { label: string; icon: keyof typeof Ionicons.glyphMap }> = {
  feed: { label: "Feed", icon: "heart" },
  calendar: { label: "Calendar", icon: "calendar" },
  "new-memory": { label: "Add", icon: "add" },
  map: { label: "Globe", icon: "globe-outline" },
  menu: { label: "Menu", icon: "restaurant" },
};

export function FloatingTabBar({ state, navigation }: BottomTabBarProps) {
  const shell = (
    <View style={styles.shell}>
      <View style={styles.island}>
        {state.routes.map((route, index) => {
          const focused = state.index === index;
          const meta = TAB_META[route.name] ?? { label: route.name, icon: "sparkles" as const };
          const isAdd = route.name === "new-memory";

          const onPress = () => {
            const event = navigation.emit({
              type: "tabPress",
              target: route.key,
              canPreventDefault: true,
            });

            if (!focused && !event.defaultPrevented) {
              navigation.navigate(route.name);
            }
          };

          return (
            <Pressable key={route.key} onPress={onPress} style={[styles.item, isAdd && styles.addItem]}>
              {isAdd ? (
                <LinearGradient colors={[theme.colors.dreamGradientStart, theme.colors.dreamGradientEnd]} style={styles.fab}>
                  <Ionicons color={theme.colors.white} name={meta.icon} size={30} />
                </LinearGradient>
              ) : focused ? (
                <LinearGradient colors={[theme.colors.dreamGradientStart, theme.colors.dreamGradientEnd]} style={styles.activePill}>
                  <Ionicons color={theme.colors.white} name={meta.icon} size={16} />
                  <Text style={styles.activeLabel}>{meta.label}</Text>
                </LinearGradient>
              ) : (
                <View style={styles.inactiveWrap}>
                  <Ionicons color={theme.colors.accent} name={meta.icon} size={18} />
                  <Text style={styles.inactiveLabel}>{meta.label}</Text>
                </View>
              )}
            </Pressable>
          );
        })}
      </View>
    </View>
  );

  if (Platform.OS === "web") {
    return shell;
  }

  return (
    <BlurView intensity={40} style={styles.blurWrap} tint="light">
      {shell}
    </BlurView>
  );
}

const styles = StyleSheet.create({
  blurWrap: {
    marginHorizontal: 18,
    marginBottom: 18,
    borderRadius: 40,
    overflow: "hidden",
  },
  shell: {
    paddingHorizontal: 10,
    paddingTop: 8,
    paddingBottom: 12,
  },
  island: {
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-around",
    minHeight: 86,
    borderRadius: 40,
    backgroundColor: "rgba(255,255,255,0.82)",
    borderWidth: 1,
    borderColor: theme.colors.border,
    ...theme.shadows.glow,
  },
  item: {
    flex: 1,
    alignItems: "center",
    justifyContent: "flex-end",
    paddingVertical: 10,
  },
  addItem: {
    marginTop: -28,
  },
  activePill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: theme.radius.pill,
  },
  activeLabel: {
    color: theme.colors.white,
    fontWeight: "800",
    fontSize: 12,
  },
  inactiveWrap: {
    alignItems: "center",
    gap: 2,
  },
  inactiveLabel: {
    color: theme.colors.textSecondary,
    fontSize: 11,
    fontWeight: "700",
  },
  fab: {
    width: 68,
    height: 68,
    borderRadius: theme.radius.pill,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 6,
    borderColor: "rgba(255,255,255,0.85)",
    ...theme.shadows.glow,
  },
});
