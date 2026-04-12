import { Redirect, Tabs } from "expo-router";
import React from "react";

import { FloatingTabBar } from "@/components/FloatingTabBar";
import { theme } from "@/constants/theme";
import { useAuth } from "@/hooks/useAuth";

export default function TabsLayout() {
  const { user, coupleSpace } = useAuth();

  if (!user) {
    return <Redirect href="/(auth)/login" />;
  }

  if (!coupleSpace) {
    return <Redirect href="/(auth)/invite" />;
  }

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        sceneStyle: {
          backgroundColor: theme.colors.background,
        },
      }}
      tabBar={(props) => <FloatingTabBar {...props} />}
    >
      <Tabs.Screen name="feed" options={{ title: "Feed" }} />
      <Tabs.Screen name="calendar" options={{ title: "Calendar" }} />
      <Tabs.Screen name="new-memory" options={{ title: "Add" }} />
      <Tabs.Screen name="map" options={{ title: "Globe" }} />
      <Tabs.Screen name="menu" options={{ title: "Menu" }} />
    </Tabs>
  );
}
