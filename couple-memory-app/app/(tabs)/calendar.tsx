import React, { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { CoupleHeader } from "@/components/CoupleHeader";
import { Screen } from "@/components/Screen";
import { SoftCard } from "@/components/SoftCard";
import { theme } from "@/constants/theme";
import { useAuth } from "@/hooks/useAuth";
import { useMemories } from "@/hooks/useMemories";
import { formatDisplayDate } from "@/utils/date";

const WEEK_DAYS = ["M", "T", "W", "T", "F", "S", "S"];

export default function CalendarScreen() {
  const { coupleSpace } = useAuth();
  const { data: memories } = useMemories(coupleSpace?.id);
  const items = memories ?? [];
  const [selectedDay, setSelectedDay] = useState<number>(new Date().getDate());

  const highlightedDays = useMemo(() => {
    return new Set(items.map((item) => new Date(item.date).getDate()).filter((value) => Number.isFinite(value)));
  }, [items]);

  const selectedMemories = items.filter((item) => new Date(item.date).getDate() === selectedDay).slice(0, 3);

  return (
    <Screen>
      <CoupleHeader
        dayCount={428}
        mini
        status="Love journal mode"
        subtitle="Keep anniversaries, tiny dates, and soft little feelings together in one sweet hand-drawn style calendar."
        title="Love calendar"
      />

      <SoftCard style={styles.heroCard}>
        <Text style={styles.heroLabel}>Today you are on</Text>
        <Text style={styles.heroNumber}>Day 428</Text>
        <Text style={styles.heroSub}>The next mini anniversary is in 7 days. Time to prepare one tiny surprise.</Text>
      </SoftCard>

      <SoftCard style={styles.calendarCard}>
        <Text style={styles.sectionTitle}>April 2026</Text>
        <View style={styles.weekRow}>
          {WEEK_DAYS.map((day) => (
            <Text key={day} style={styles.weekLabel}>
              {day}
            </Text>
          ))}
        </View>
        <View style={styles.grid}>
          {Array.from({ length: 30 }).map((_, index) => {
            const day = index + 1;
            const selected = day === selectedDay;
            const highlighted = highlightedDays.has(day);
            return (
              <Pressable
                key={day}
                onPress={() => setSelectedDay(day)}
                style={[styles.dayCell, highlighted && styles.dayCellMarked, selected && styles.dayCellSelected]}
              >
                <Text style={[styles.dayText, selected && styles.dayTextSelected]}>{day}</Text>
                {highlighted ? <View style={[styles.dot, selected && styles.dotSelected]} /> : null}
              </Pressable>
            );
          })}
        </View>
      </SoftCard>

      <SoftCard style={styles.summaryCard}>
        <Text style={styles.sectionTitle}>Memories on this day</Text>
        {selectedMemories.length ? (
          selectedMemories.map((memory) => (
            <View key={memory.id} style={styles.summaryItem}>
              <Text style={styles.summaryTitle}>{memory.title}</Text>
              <Text style={styles.summaryMeta}>
                {formatDisplayDate(memory.date)} · {memory.place_name}
              </Text>
              <Text numberOfLines={2} style={styles.summaryText}>
                {memory.note || "There is a little memory here already, even if the note has not been written yet."}
              </Text>
            </View>
          ))
        ) : (
          <Text style={styles.summaryText}>Nothing is pinned to this day yet. Leave it for the next sweet date.</Text>
        )}
      </SoftCard>
    </Screen>
  );
}

const styles = StyleSheet.create({
  heroCard: {
    gap: theme.spacing.xs,
    alignItems: "center",
  },
  heroLabel: {
    color: theme.colors.textMuted,
    fontWeight: "700",
  },
  heroNumber: {
    color: theme.colors.primary,
    fontSize: 42,
    fontWeight: "900",
  },
  heroSub: {
    color: theme.colors.text,
    textAlign: "center",
    lineHeight: 22,
  },
  calendarCard: {
    gap: theme.spacing.md,
  },
  sectionTitle: {
    color: theme.colors.text,
    fontSize: 18,
    fontWeight: "800",
  },
  weekRow: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  weekLabel: {
    width: "14%",
    textAlign: "center",
    color: theme.colors.textMuted,
    fontWeight: "700",
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  dayCell: {
    width: "13%",
    aspectRatio: 1,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.58)",
    gap: 4,
  },
  dayCellMarked: {
    backgroundColor: "rgba(255,236,245,0.92)",
  },
  dayCellSelected: {
    backgroundColor: theme.colors.primary,
  },
  dayText: {
    color: theme.colors.text,
    fontWeight: "700",
  },
  dayTextSelected: {
    color: theme.colors.white,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: theme.colors.primary,
  },
  dotSelected: {
    backgroundColor: theme.colors.white,
  },
  summaryCard: {
    gap: theme.spacing.md,
  },
  summaryItem: {
    gap: 4,
    paddingBottom: 10,
  },
  summaryTitle: {
    color: theme.colors.text,
    fontWeight: "800",
  },
  summaryMeta: {
    color: theme.colors.primary,
    fontSize: 12,
    fontWeight: "700",
  },
  summaryText: {
    color: theme.colors.textMuted,
    lineHeight: 21,
  },
});
