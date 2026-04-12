import { GradientButton } from "@/components/GradientButton";
import React from "react";

type Props = {
  title: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "ghost";
  disabled?: boolean;
  loading?: boolean;
};

export function AppButton({
  title,
  onPress,
  variant = "primary",
  disabled,
  loading,
}: Props) {
  return (
    <GradientButton
      disabled={disabled}
      loading={loading}
      onPress={onPress}
      title={title}
      variant={variant}
    />
  );
}
