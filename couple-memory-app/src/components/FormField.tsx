import React from "react";
import { StyleSheet, Text, TextInput, TextInputProps } from "react-native";

import { SoftCard } from "@/components/SoftCard";
import { theme } from "@/constants/theme";

type Props = TextInputProps & {
  label: string;
  hint?: string;
};

export function FormField({ label, hint, style, ...props }: Props) {
  return (
    <SoftCard style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        placeholderTextColor={theme.colors.textMuted}
        style={[styles.input, props.multiline && styles.multiline, style]}
        {...props}
      />
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </SoftCard>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    gap: theme.spacing.xs,
  },
  label: {
    fontSize: 14,
    fontWeight: "700",
    color: theme.colors.text,
  },
  input: {
    minHeight: 52,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.72)",
    backgroundColor: "rgba(255,255,255,0.7)",
    paddingHorizontal: 14,
    color: theme.colors.text,
    fontSize: 15,
  },
  multiline: {
    minHeight: 110,
    textAlignVertical: "top",
    paddingTop: 14,
  },
  hint: {
    color: theme.colors.textMuted,
    fontSize: 12,
  },
});
