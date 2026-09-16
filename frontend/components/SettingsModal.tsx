"use client";

import { useEffect } from "react";
import type { ThemeId } from "@/lib/themes";

type SettingsModalProps = {
  open: boolean;
  theme: ThemeId;
  onThemeChange: (theme: ThemeId) => void;
  onClose: () => void;
};

const themeOptions: Array<{
  id: ThemeId;
  name: string;
  description: string;
  preview: string;
}> = [
  {
    id: "midnight" as ThemeId,
    name: "Midnight",
    description: "The classic dark LocalGPT experience",
    preview: "#202020",
  },
  {
    id: "ocean" as ThemeId,
    name: "Ocean",
    description: "Cool blue tones with a calm interface",
    preview: "#12304d",
  },
  {
    id: "forest" as ThemeId,
    name: "Forest",
    description: "Natural green tones",
    preview: "#142b23",
  },
  {
    id: "royal" as ThemeId,
    name: "Royal",
    description: "Elegant purple and indigo colors",
    preview: "#241d40",
  },
  {
    id: "sunset" as ThemeId,
    name: "Sunset",
    description: "Warm orange and brown tones",
    preview: "#38241b",
  },
  {
    id: "rose" as ThemeId,
    name: "Rose",
    description: "Soft pink and wine colors",
    preview: "#351d2d",
  },
  {
    id: "light" as ThemeId,
    name: "Light",
    description: "A clean bright interface",
    preview: "#f5f5f5",
  },
  {
    id: "slate" as ThemeId,
    name: "Slate",
    description: "Neutral gray professional theme",
    preview: "#202631",
  },
];

export default function SettingsModal({
  open,
  theme,
  onThemeChange,
  onClose,
}: SettingsModalProps) {
  useEffect(() => {
    if (!open) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
        className="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] shadow-2xl"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="flex items-start justify-between border-b border-[var(--border)] px-6 py-5">
          <div>
            <h2 id="settings-title" className="text-2xl font-semibold">
              Settings
            </h2>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">
              Customize your LocalGPT experience
            </p>
          </div>

          <button
            type="button"
            aria-label="Close settings"
            onClick={onClose}
            className="flex h-11 w-11 items-center justify-center rounded-xl text-2xl text-[var(--text-secondary)] transition hover:bg-[var(--background)] hover:text-[var(--text-primary)]"
          >
            ×
          </button>
        </header>

        <div className="overflow-y-auto px-6 py-6">
          <div className="mb-5">
            <h3 className="text-lg font-semibold">Appearance</h3>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">
              Choose a theme for the complete application.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {themeOptions.map((option) => {
              const selected = theme === option.id;

              return (
                <button
                  key={String(option.id)}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => onThemeChange(option.id)}
                  className={`flex items-center gap-4 rounded-2xl border p-4 text-left transition ${
                    selected
                      ? "border-[var(--accent)] bg-[var(--background)] ring-2 ring-[var(--accent)]"
                      : "border-[var(--border)] hover:border-[var(--accent)] hover:bg-[var(--background)]"
                  }`}
                >
                  <span
                    aria-hidden="true"
                    className="h-16 w-16 shrink-0 rounded-xl border border-white/10 shadow-inner"
                    style={{ backgroundColor: option.preview }}
                  />

                  <span className="min-w-0">
                    <span className="block text-base font-semibold">
                      {option.name}
                    </span>
                    <span className="mt-1 block text-sm text-[var(--text-secondary)]">
                      {option.description}
                    </span>
                  </span>

                  {selected && (
                    <span
                      aria-hidden="true"
                      className="ml-auto self-start text-lg text-[var(--accent)]"
                    >
                      ✓
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        <footer className="flex justify-end border-t border-[var(--border)] px-6 py-5">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-[var(--accent)] px-6 py-3 font-medium text-white transition hover:opacity-90"
          >
            Done
          </button>
        </footer>
      </section>
    </div>
  );
}
