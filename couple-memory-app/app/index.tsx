import { Redirect } from "expo-router";
import React from "react";
import { ActivityIndicator, View } from "react-native";

import { theme } from "@/constants/theme";
import { useAuth } from "@/hooks/useAuth";

export default function IndexScreen() {
  const { initialized, user, coupleSpace } = useAuth();

  if (!initialized) {
    return (
      <View
        style={{
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: theme.colors.background,
        }}
      >
        <ActivityIndicator color={theme.colors.primary} />
      </View>
    );
  }

  if (!user) {
    return <Redirect href="/(auth)/login" />;
  }

  if (!coupleSpace) {
    return <Redirect href="/(auth)/invite" />;
  }

  return <Redirect href="/(tabs)/feed" />;
}
