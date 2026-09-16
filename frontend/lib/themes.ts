export type ThemeId =
  | "midnight"
  | "ocean"
  | "forest"
  | "royal"
  | "sunset"
  | "rose"
  | "light"
  | "slate";

export type ThemeDefinition = {
  id: ThemeId;
  name: string;
  description: string;
  preview: string;
};

export const THEMES: ThemeDefinition[] = [
  {
    id: "midnight",
    name: "Midnight",
    description: "The classic dark LocalGPT experience",
    preview: "#212121",
  },
  {
    id: "ocean",
    name: "Ocean",
    description: "Cool blue tones with a calm interface",
    preview: "#102a43",
  },
  {
    id: "forest",
    name: "Forest",
    description: "Natural green tones",
    preview: "#17251f",
  },
  {
    id: "royal",
    name: "Royal",
    description: "Elegant purple and indigo colors",
    preview: "#211b36",
  },
  {
    id: "sunset",
    name: "Sunset",
    description: "Warm orange and brown colors",
    preview: "#302019",
  },
  {
    id: "rose",
    name: "Rose",
    description: "Soft pink and wine colors",
    preview: "#301d28",
  },
  {
    id: "light",
    name: "Light",
    description: "A clean bright interface",
    preview: "#f7f7f8",
  },
  {
    id: "slate",
    name: "Slate",
    description: "Neutral gray professional theme",
    preview: "#20242b",
  },
];