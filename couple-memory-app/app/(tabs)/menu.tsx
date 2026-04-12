import React, { useState } from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";

import { CoupleHeader } from "@/components/CoupleHeader";
import { GradientButton } from "@/components/GradientButton";
import { MoodChip } from "@/components/MoodChip";
import { Screen } from "@/components/Screen";
import { SoftCard } from "@/components/SoftCard";
import { theme } from "@/constants/theme";

const CATEGORIES = ["奶茶", "甜品", "火锅", "烧烤", "日料", "韩料", "夜宵"];
const ITEMS = [
  {
    id: "1",
    name: "草莓奶云冰",
    tags: ["甜甜的", "约会感"],
    price: "￥28-38",
    craving: "想吃指数 97%",
    image: "https://images.unsplash.com/photo-1551024601-bec78aea704b?q=80&w=800&auto=format&fit=crop",
  },
  {
    id: "2",
    name: "深夜小火锅",
    tags: ["热乎乎", "贴贴"],
    price: "￥88-128",
    craving: "想吃指数 95%",
    image: "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=800&auto=format&fit=crop",
  },
];

export default function MenuScreen() {
  const [selected, setSelected] = useState("奶茶");

  return (
    <Screen>
      <CoupleHeader
        mini
        status="约会菜单"
        subtitle="今天想吃什么呀，把纠结交给这张软糯糯的小菜单板"
        title="可爱约会菜单"
      />

      <SoftCard style={styles.categoryCard}>
        <Text style={styles.sectionTitle}>今天想吃什么呀</Text>
        <View style={styles.categoryRow}>
          {CATEGORIES.map((item) => {
            const active = item === selected;
            return (
              <Pressable key={item} onPress={() => setSelected(item)} style={[styles.categoryChip, active && styles.categoryChipActive]}>
                <Text style={[styles.categoryText, active && styles.categoryTextActive]}>{item}</Text>
              </Pressable>
            );
          })}
        </View>
      </SoftCard>

      {ITEMS.map((item) => (
        <SoftCard key={item.id} style={styles.menuCard}>
          <Image source={{ uri: item.image }} style={styles.cover} />
          <View style={styles.menuBody}>
            <Text style={styles.menuTitle}>{item.name}</Text>
            <View style={styles.tagRow}>
              {item.tags.map((tag) => (
                <MoodChip key={tag} icon="✦" label={tag} />
              ))}
            </View>
            <Text style={styles.menuMeta}>{item.price}</Text>
            <Text style={styles.menuHint}>{item.craving}</Text>
            <View style={styles.actions}>
              <GradientButton onPress={() => undefined} title="想吃" variant="secondary" />
              <GradientButton onPress={() => undefined} title="今天就吃它" />
            </View>
          </View>
        </SoftCard>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  categoryCard: {
    gap: theme.spacing.md,
  },
  sectionTitle: {
    color: theme.colors.text,
    fontSize: 18,
    fontWeight: "800",
  },
  categoryRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  categoryChip: {
    borderRadius: theme.radius.pill,
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: "rgba(255,255,255,0.66)",
  },
  categoryChipActive: {
    backgroundColor: "#FFE7F3",
  },
  categoryText: {
    color: theme.colors.textMuted,
    fontWeight: "700",
  },
  categoryTextActive: {
    color: theme.colors.primary,
  },
  menuCard: {
    gap: theme.spacing.md,
  },
  cover: {
    width: "100%",
    height: 190,
    borderRadius: 24,
    backgroundColor: theme.colors.backgroundSecondary,
  },
  menuBody: {
    gap: theme.spacing.sm,
  },
  menuTitle: {
    color: theme.colors.text,
    fontSize: 20,
    fontWeight: "800",
  },
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  menuMeta: {
    color: theme.colors.primary,
    fontWeight: "700",
  },
  menuHint: {
    color: theme.colors.textMuted,
  },
  actions: {
    gap: 10,
  },
});
