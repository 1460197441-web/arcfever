import type { Memory } from "@/types/domain";

export function getRegionFromMemories(memories: Memory[], fallback: { lat: number; lng: number }) {
  if (!memories.length) {
    return {
      latitude: fallback.lat,
      longitude: fallback.lng,
      latitudeDelta: 0.08,
      longitudeDelta: 0.08,
    };
  }

  const lats = memories.map((item) => item.lat);
  const lngs = memories.map((item) => item.lng);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);

  return {
    latitude: (minLat + maxLat) / 2,
    longitude: (minLng + maxLng) / 2,
    latitudeDelta: Math.max(maxLat - minLat, 0.05) * 1.6,
    longitudeDelta: Math.max(maxLng - minLng, 0.05) * 1.6,
  };
}

export function normalizePoints(memories: Memory[]) {
  if (!memories.length) {
    return [];
  }

  const lats = memories.map((item) => item.lat);
  const lngs = memories.map((item) => item.lng);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);

  return memories.map((memory) => {
    const x = maxLng === minLng ? 50 : ((memory.lng - minLng) / (maxLng - minLng)) * 100;
    const y = maxLat === minLat ? 50 : 100 - ((memory.lat - minLat) / (maxLat - minLat)) * 100;

    return {
      ...memory,
      x,
      y,
    };
  });
}
