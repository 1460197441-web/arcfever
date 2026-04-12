import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import React from "react";

import { theme } from "@/constants/theme";
import { AuthProvider } from "@/store/auth-store";

const queryClient = new QueryClient();

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerStyle: {
              backgroundColor: theme.colors.background,
            },
            headerShadowVisible: false,
            headerTintColor: theme.colors.text,
            headerTitleStyle: {
              fontWeight: "700",
            },
            contentStyle: {
              backgroundColor: theme.colors.background,
            },
          }}
        >
          <Stack.Screen name="index" options={{ headerShown: false }} />
          <Stack.Screen name="(auth)/login" options={{ title: "Login" }} />
          <Stack.Screen name="(auth)/invite" options={{ title: "Invite" }} />
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="memory/[id]" options={{ title: "Memory detail" }} />
          <Stack.Screen name="memory/[id]/edit" options={{ title: "Edit memory" }} />
        </Stack>
      </AuthProvider>
    </QueryClientProvider>
  );
}
