import { env, isSupabaseConfigured } from "@/lib/env";
import { supabase } from "@/lib/supabase";
import * as ImageManipulator from "expo-image-manipulator";

const SIGNED_URL_TTL_SECONDS = 60 * 60;
const MAX_UPLOAD_WIDTH = 1600;
const JPEG_QUALITY = 0.72;

function sanitizeFileName(fileName: string) {
  return fileName.replace(/[^a-zA-Z0-9._-]/g, "-");
}

function isDirectUri(value: string) {
  return /^(https?:|file:|blob:|data:|content:)/.test(value);
}

function isHttpUrl(value: string) {
  return /^https?:/i.test(value);
}

function getFileExtension(uri: string, fallback = "jpg") {
  const clean = uri.split("?")[0] ?? uri;
  const match = clean.match(/\.([a-zA-Z0-9]+)$/);
  return match?.[1]?.toLowerCase() || fallback;
}

export function createMemoryId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  const bytes = Array.from({ length: 16 }, () => Math.floor(Math.random() * 256));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = bytes.map((value) => value.toString(16).padStart(2, "0"));
  return `${hex.slice(0, 4).join("")}-${hex.slice(4, 6).join("")}-${hex.slice(6, 8).join("")}-${hex.slice(8, 10).join("")}-${hex.slice(10, 16).join("")}`;
}

export function buildMemoryPhotoPath(params: {
  coupleSpaceId: string;
  memoryId: string;
  sourceUri: string;
  index: number;
}) {
  const extension = getFileExtension(params.sourceUri);
  const uniquePart = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const fileName = sanitizeFileName(`photo-${params.index + 1}-${uniquePart}.${extension}`);
  return `${params.coupleSpaceId}/${params.memoryId}/${fileName}`;
}

export async function uploadPrivateMemoryPhoto(params: {
  sourceUri: string;
  coupleSpaceId: string;
  memoryId: string;
  index: number;
}) {
  if (!supabase) {
    return params.sourceUri;
  }

  if (!isDirectUri(params.sourceUri)) {
    return params.sourceUri;
  }

  if (isHttpUrl(params.sourceUri)) {
    throw new Error("Remote image URLs are not allowed for private uploads.");
  }

  const manipulated = await ImageManipulator.manipulateAsync(
    params.sourceUri,
    [{ resize: { width: MAX_UPLOAD_WIDTH } }],
    {
      compress: JPEG_QUALITY,
      format: ImageManipulator.SaveFormat.JPEG,
    },
  );

  const response = await fetch(manipulated.uri);
  const blob = await response.blob();
  const arrayBuffer = await blob.arrayBuffer();
  const path = buildMemoryPhotoPath({
    coupleSpaceId: params.coupleSpaceId,
    memoryId: params.memoryId,
    sourceUri: manipulated.uri,
    index: params.index,
  });

  const { error } = await supabase.storage.from(env.memoryBucket).upload(path, arrayBuffer, {
    contentType: blob.type || "image/jpeg",
    upsert: true,
  });

  if (error) {
    throw error;
  }

  return path;
}

export async function resolvePhotoUrls(photoRefs: string[]) {
  if (!photoRefs.length) {
    return [] as string[];
  }

  if (!isSupabaseConfigured || !supabase) {
    return photoRefs;
  }

  const directUrls = new Map<string, string>();
  const storagePaths: string[] = [];

  for (const photoRef of photoRefs) {
    if (isDirectUri(photoRef)) {
      directUrls.set(photoRef, photoRef);
    } else {
      storagePaths.push(photoRef);
    }
  }

  if (!storagePaths.length) {
    return photoRefs;
  }

  const { data, error } = await (supabase as any).storage
    .from(env.memoryBucket)
    .createSignedUrls(storagePaths, SIGNED_URL_TTL_SECONDS);

  if (error) {
    throw error;
  }

  const signedUrlMap = new Map<string, string>();
  for (const item of data ?? []) {
    if (item.path && item.signedUrl) {
      signedUrlMap.set(item.path, item.signedUrl);
    }
  }

  return photoRefs
    .map((photoRef) => directUrls.get(photoRef) ?? signedUrlMap.get(photoRef) ?? null)
    .filter((item): item is string => Boolean(item));
}

export async function deletePrivateMemoryFiles(photoRefs: string[]) {
  const storagePaths = photoRefs.filter((photoRef) => !isDirectUri(photoRef));

  if (!storagePaths.length || !supabase) {
    return { failedPaths: [] as string[] };
  }

  const { data, error } = await (supabase as any).storage.from(env.memoryBucket).remove(storagePaths);

  if (error) {
    return { failedPaths: storagePaths };
  }

  if (!data || data.length === 0) {
    return { failedPaths: [] as string[] };
  }

  const deleted = new Set<string>(
    (data ?? [])
      .map((item: { name?: string }) => item.name)
      .filter((item: string | undefined): item is string => Boolean(item)),
  );
  const failedPaths = storagePaths.filter((path) => {
    const fileName = path.split("/").pop();
    return fileName ? !deleted.has(fileName) : true;
  });
  return { failedPaths };
}
