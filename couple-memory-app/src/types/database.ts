export type Database = {
  public: {
    Tables: {
      couple_members: {
        Row: {
          id: string;
          couple_space_id: string;
          user_id: string;
          role: "owner" | "partner";
          joined_at: string;
        };
        Insert: {
          id?: string;
          couple_space_id: string;
          user_id: string;
          role: "owner" | "partner";
          joined_at?: string;
        };
        Update: Partial<Database["public"]["Tables"]["couple_members"]["Insert"]>;
      };
      couple_spaces: {
        Row: {
          id: string;
          name: string;
          invite_code: string;
          owner_user_id: string;
          max_members: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          name: string;
          invite_code?: string;
          owner_user_id: string;
          max_members?: number;
          created_at?: string;
        };
        Update: Partial<Database["public"]["Tables"]["couple_spaces"]["Insert"]>;
      };
      memories: {
        Row: {
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
        Insert: {
          id?: string;
          title: string;
          date: string;
          place_name: string;
          lat: number;
          lng: number;
          note?: string;
          photos?: string[];
          author_id: string;
          couple_space_id: string;
          created_at?: string;
          updated_at?: string;
        };
        Update: Partial<Database["public"]["Tables"]["memories"]["Insert"]>;
      };
      memory_photos: {
        Row: {
          id: string;
          memory_id: string;
          couple_space_id: string;
          storage_path: string;
          sort_order: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          memory_id: string;
          couple_space_id: string;
          storage_path: string;
          sort_order?: number;
          created_at?: string;
        };
        Update: Partial<Database["public"]["Tables"]["memory_photos"]["Insert"]>;
      };
      profiles: {
        Row: {
          id: string;
          email: string;
          display_name: string | null;
          avatar_url: string | null;
          created_at: string;
        };
        Insert: {
          id: string;
          email: string;
          display_name?: string | null;
          avatar_url?: string | null;
          created_at?: string;
        };
        Update: Partial<Database["public"]["Tables"]["profiles"]["Insert"]>;
      };
    };
    Functions: {
      create_couple_space: {
        Args: { p_name: string };
        Returns: string;
      };
      delete_memory_with_photo_refs: {
        Args: { p_memory_id: string };
        Returns: string[];
      };
      join_couple_space: {
        Args: { p_invite_code: string };
        Returns: string;
      };
      replace_memory_photo_refs: {
        Args: { p_memory_id: string; p_photo_paths: string[] };
        Returns: Database["public"]["Tables"]["memories"]["Row"];
      };
    };
  };
};
