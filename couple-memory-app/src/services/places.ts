import { env } from "@/lib/env";

export function getInitialMapCenter() {
  return {
    lat: env.mapInitialLat,
    lng: env.mapInitialLng,
  };
}
