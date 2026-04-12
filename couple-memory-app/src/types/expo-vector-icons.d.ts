declare module "@expo/vector-icons" {
  import type { ReactElement } from "react";
  import type { TextProps } from "react-native";

  export type IconProps<Name extends string> = TextProps & {
    name: Name;
    size?: number;
    color?: string;
  };

  export type IconComponent<Name extends string> = ((props: IconProps<Name>) => ReactElement | null) & {
    glyphMap: Record<Name, number | string>;
  };

  export const Ionicons: IconComponent<string>;
}
