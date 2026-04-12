import React from "react";
import { Platform, StyleSheet, View, ViewProps } from "react-native";
import { BlurView } from "expo-blur";

import { colors, radius, shadow } from "@/theme/loveTheme";

export function SoftCard({ style, children, ...props }: ViewProps) {
  if (Platform.OS === "web") {
    return (
      <View style={[styles.wrap, styles.webCard, style]} {...props}>
        {children}
      </View>
    );
  }

  return (
    <View style={[styles.wrap, style]} {...props}>
      <BlurView intensity={20} tint="light" style={styles.card}>
        {children}
      </BlurView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderRadius: radius.xxl,
    overflow: "hidden",
    backgroundColor: "rgba(255,255,255,0.22)",
    ...shadow.frosting,
  },
  webCard: {
    backgroundColor: colors.whiteGlass,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.xxl,
    padding: 18,
  },
  card: {
    backgroundColor: colors.whiteGlass,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.xxl,
    padding: 18,
  },
});
