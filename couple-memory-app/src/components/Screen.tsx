import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { SafeAreaView, ScrollView, StyleSheet, View, ViewStyle } from "react-native";

import { theme } from "@/constants/theme";

type Props = React.PropsWithChildren<{
  scroll?: boolean;
  contentStyle?: ViewStyle;
}>;

export function Screen({ children, scroll = true, contentStyle }: Props) {
  if (!scroll) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <BackgroundDecor />
        <View style={[styles.fill, contentStyle]}>{children}</View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <BackgroundDecor />
      <ScrollView contentContainerStyle={[styles.content, contentStyle]} showsVerticalScrollIndicator={false}>
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

function BackgroundDecor() {
  return (
    <LinearGradient
      colors={[theme.colors.background, theme.colors.backgroundSecondary, theme.colors.backgroundLayer]}
      style={StyleSheet.absoluteFill}
    >
      <View style={styles.blobTop} />
      <View style={styles.blobMiddle} />
      <View style={styles.blobBottom} />
      <View style={styles.sparkleWrap}>
        <View style={styles.sparkleDot} />
        <View style={[styles.sparkleDot, styles.sparkleDotAlt]} />
      </View>
      <View style={styles.heartWrap}>
        <View style={styles.heartBubble} />
        <View style={[styles.heartBubble, styles.heartBubbleAlt]} />
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  fill: {
    flex: 1,
    padding: theme.spacing.lg,
  },
  content: {
    padding: theme.spacing.lg,
    gap: theme.spacing.md,
    paddingBottom: 120,
  },
  blobTop: {
    position: "absolute",
    top: -40,
    right: -30,
    width: 170,
    height: 170,
    borderRadius: 85,
    backgroundColor: "rgba(248,182,216,0.35)",
  },
  blobMiddle: {
    position: "absolute",
    top: 220,
    left: -55,
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: "rgba(235,213,255,0.34)",
  },
  blobBottom: {
    position: "absolute",
    bottom: 40,
    left: -40,
    width: 150,
    height: 150,
    borderRadius: 75,
    backgroundColor: "rgba(217,184,255,0.24)",
  },
  sparkleWrap: {
    position: "absolute",
    top: 90,
    left: 26,
  },
  sparkleDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "rgba(255,182,214,0.55)",
  },
  sparkleDotAlt: {
    marginTop: 22,
    marginLeft: 18,
    backgroundColor: "rgba(185,147,255,0.4)",
  },
  heartWrap: {
    position: "absolute",
    top: 130,
    right: 28,
    gap: 14,
  },
  heartBubble: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: "rgba(255,255,255,0.28)",
    transform: [{ rotate: "45deg" }],
  },
  heartBubbleAlt: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginLeft: 24,
    backgroundColor: "rgba(255,182,214,0.35)",
  },
});
