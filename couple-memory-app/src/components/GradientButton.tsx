import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { theme } from "@/constants/theme";

type Props = {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: "primary" | "secondary" | "ghost";
};

export function GradientButton({
  title,
  onPress,
  disabled,
  loading,
  variant = "primary",
}: Props) {
  const isDisabled = disabled || loading;

  return (
    <Pressable disabled={isDisabled} onPress={onPress} style={({ pressed }) => [pressed && !isDisabled && styles.pressed]}>
      {variant === "primary" ? (
        <LinearGradient
          colors={[theme.colors.dreamGradientStart, theme.colors.dreamGradientEnd]}
          end={{ x: 1, y: 1 }}
          start={{ x: 0, y: 0 }}
          style={[styles.base, styles.primary, isDisabled && styles.disabled]}
        >
          {loading ? <ActivityIndicator color={theme.colors.white} /> : <Text style={styles.primaryLabel}>{title}</Text>}
        </LinearGradient>
      ) : (
        <View
          style={[
            styles.base,
            variant === "secondary" ? styles.secondary : styles.ghost,
            isDisabled && styles.disabled,
          ]}
        >
          {loading ? (
            <ActivityIndicator color={theme.colors.textPrimary} />
          ) : (
            <Text style={variant === "secondary" ? styles.secondaryLabel : styles.ghostLabel}>{title}</Text>
          )}
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: 54,
    borderRadius: theme.radius.pill,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: theme.spacing.xl,
  },
  primary: {
    ...theme.shadows.glow,
  },
  secondary: {
    backgroundColor: "rgba(255,255,255,0.78)",
    borderWidth: 1,
    borderColor: theme.colors.border,
    ...theme.shadows.soft,
  },
  ghost: {
    backgroundColor: "transparent",
  },
  disabled: {
    opacity: 0.6,
  },
  pressed: {
    opacity: 0.92,
    transform: [{ scale: 0.99 }],
  },
  primaryLabel: {
    color: theme.colors.white,
    fontWeight: "800",
    fontSize: 16,
  },
  secondaryLabel: {
    color: theme.colors.textPrimary,
    fontWeight: "700",
    fontSize: 15,
  },
  ghostLabel: {
    color: theme.colors.textSecondary,
    fontWeight: "700",
    fontSize: 15,
  },
});
