export type AppUser = {
  id: string;
  email: string;
  displayName?: string | null;
};

export type CoupleSpace = {
  id: string;
  name: string;
  invite_code: string;
  owner_user_id: string;
  max_members: number;
  created_at: string;
};

export type CoupleMember = {
  id: string;
  couple_space_id: string;
  user_id: string;
  role: "owner" | "partner";
  joined_at: string;
};

export type Memory = {
  id: string;
  title: string;
  date: string;
  place_name: string;
  lat: number;
  lng: number;
  note: string;
  photos: string[];
  author_id: string;
  couple_space_id: string;
  created_at: string;
  updated_at: string;
};

export type CreateMemoryInput = Omit<
  Memory,
  "id" | "created_at" | "updated_at"
>;

export type UpdateMemoryFieldsInput = Pick<
  Memory,
  "title" | "date" | "place_name" | "lat" | "lng" | "note"
>;
