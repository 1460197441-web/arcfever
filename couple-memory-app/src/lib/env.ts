import Constants from "expo-constants";

const extra = (Constants.expoConfig?.extra ?? {}) as Record<string, string | undefined>;

function readValue(name: string, fallbackKey?: string) {
  return process.env[name] ?? (fallbackKey ? extra[fallbackKey] : undefined) ?? "";
}

export const env = {
  supabaseUrl: readValue("EXPO_PUBLIC_SUPABASE_URL", "supabaseUrl"),
  supabaseAnonKey: readValue("EXPO_PUBLIC_SUPABASE_ANON_KEY", "supabaseAnonKey"),
  memoryBucket: readValue("EXPO_PUBLIC_SUPABASE_MEMORY_BUCKET", "memoryBucket") || "memory-photos",
  mapInitialLat: Number(readValue("EXPO_PUBLIC_MAP_INITIAL_LAT", "mapInitialLat") || "31.2304"),
  mapInitialLng: Number(readValue("EXPO_PUBLIC_MAP_INITIAL_LNG", "mapInitialLng") || "121.4737"),
  devLoginCode: readValue("EXPO_PUBLIC_DEV_LOGIN_CODE", "devLoginCode") || "246810",
};

export const isSupabaseConfigured = Boolean(env.supabaseUrl && env.supabaseAnonKey);
