"use client";

type VoiceRecordingPanelProps = {
  waveform: number[];
  elapsedSeconds: number;
  isTranscribing: boolean;
  onCancel: () => void;
  onStop: () => void;
};

function CloseIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path d="M6 6l12 12" />
      <path d="M18 6L6 18" />
    </svg>
  );
}

function StopIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <rect
        x="6"
        y="6"
        width="12"
        height="12"
        rx="2.5"
      />
    </svg>
  );
}

function formatRecordingTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  return `${minutes
    .toString()
    .padStart(2, "0")}:${remainingSeconds
    .toString()
    .padStart(2, "0")}`;
}

export default function VoiceRecordingPanel({
  waveform,
  elapsedSeconds,
  isTranscribing,
  onCancel,
  onStop,
}: VoiceRecordingPanelProps) {
  return (
    <div className="relative flex min-h-[72px] w-full items-center gap-3 rounded-[28px] bg-[var(--surface)] px-3 shadow-sm">
      {/* Cancel */}
      <button
        type="button"
        onClick={onCancel}
        disabled={isTranscribing}
        aria-label="Cancel recording"
        title="Cancel recording"
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-[#454545] text-[#b4b4b4] transition hover:bg-[#353535] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
      >
        <CloseIcon />
      </button>

      {/* Center */}
      <div className="flex min-w-0 flex-1 items-center gap-3">
        {isTranscribing ? (
          <>
            <div className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#b4b4b4]" />
              <span
                className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#b4b4b4]"
                style={{ animationDelay: "120ms" }}
              />
              <span
                className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#b4b4b4]"
                style={{ animationDelay: "240ms" }}
              />
            </div>

            <span className="text-sm text-[#b4b4b4]">
              Transcribing...
            </span>
          </>
        ) : (
          <>
            {/* Live waveform */}
            <div className="flex h-12 min-w-0 flex-1 items-center justify-center gap-[3px] overflow-hidden">
              {waveform.map((level, index) => {
                const height = Math.max(
                  4,
                  Math.min(40, level * 44),
                );

                return (
                  <span
                    key={index}
                    className="w-[3px] shrink-0 rounded-full bg-[#9b9b9b] transition-[height,opacity] duration-75"
                    style={{
                      height: `${height}px`,
                      opacity: 0.45 + level * 0.55,
                    }}
                  />
                );
              })}
            </div>

            <span className="shrink-0 font-mono text-xs tabular-nums text-[#8e8e8e]">
              {formatRecordingTime(elapsedSeconds)}
            </span>
          </>
        )}
      </div>

      {/* Stop */}
      <button
        type="button"
        onClick={onStop}
        disabled={isTranscribing}
        aria-label="Stop recording"
        title="Stop recording"
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-[#454545] text-white transition hover:bg-[#353535] disabled:cursor-not-allowed disabled:opacity-40"
      >
        <StopIcon />
      </button>
    </div>
  );
}