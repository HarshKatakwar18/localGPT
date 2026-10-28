"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type UseAudioRecorderResult = {
  isRecording: boolean;
  elapsedSeconds: number;
  waveform: number[];
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  cancelRecording: () => void;
};

const WAVEFORM_BARS = 36;

function createIdleWaveform(): number[] {
  return Array.from(
    { length: WAVEFORM_BARS },
    () => 0.08,
  );
}

export function useAudioRecorder(): UseAudioRecorderResult {
  const [isRecording, setIsRecording] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [waveform, setWaveform] = useState<number[]>(
    createIdleWaveform,
  );
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  const animationFrameRef = useRef<number | null>(null);

  const chunksRef = useRef<Blob[]>([]);
  const discardRef = useRef(false);

  /*
   * ---------------------------------------------------------
   * Cleanup audio resources
   * ---------------------------------------------------------
   */
  const cleanupAudio = useCallback(() => {
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    streamRef.current?.getTracks().forEach((track) => {
      track.stop();
    });

    streamRef.current = null;

    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    analyserRef.current = null;
  }, []);

  /*
   * ---------------------------------------------------------
   * Start recording
   * ---------------------------------------------------------
   */
  const startRecording = useCallback(async () => {
    if (isRecording) {
      return;
    }

    setError(null);
    setElapsedSeconds(0);
    setWaveform(createIdleWaveform());

    discardRef.current = false;
    chunksRef.current = [];

    try {
      /*
       * Check browser microphone support.
       */
      if (
        typeof navigator === "undefined" ||
        !navigator.mediaDevices?.getUserMedia
      ) {
        throw new Error(
          "Microphone recording is not supported in this browser.",
        );
      }

      /*
       * Request microphone access.
       */
      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });

      streamRef.current = stream;

      /*
       * Select supported recording format.
       */
      const mimeTypes = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
      ];

      const supportedMimeType = mimeTypes.find(
        (type) => MediaRecorder.isTypeSupported(type),
      );

      const recorder = supportedMimeType
        ? new MediaRecorder(stream, {
            mimeType: supportedMimeType,
          })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = recorder;

      /*
       * Collect audio chunks.
       */
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      /*
       * Start recording.
       */
      recorder.start(250);

      /*
       * -----------------------------------------------------
       * Create audio analyser for waveform visualization.
       * -----------------------------------------------------
       */
      const AudioContextClass =
        window.AudioContext ||
        (
          window as typeof window & {
            webkitAudioContext?: typeof AudioContext;
          }
        ).webkitAudioContext;

      if (AudioContextClass) {
        const audioContext = new AudioContextClass();

        if (audioContext.state === "suspended") {
          await audioContext.resume();
        }

        const analyser =
          audioContext.createAnalyser();

        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.72;
        analyser.minDecibels = -90;
        analyser.maxDecibels = -10;

        const source =
          audioContext.createMediaStreamSource(stream);

        source.connect(analyser);

        audioContextRef.current = audioContext;
        analyserRef.current = analyser;
      }

      /*
       * Switch UI into recording mode.
       */
      setIsRecording(true);
    } catch (err) {
      cleanupAudio();

      const message =
        err instanceof DOMException &&
        err.name === "NotAllowedError"
          ? "Microphone permission was denied."
          : err instanceof Error
            ? err.message
            : "Unable to start microphone recording.";

      setError(message);
      setIsRecording(false);
    }
  }, [
    cleanupAudio,
    isRecording,
  ]);

  /*
   * ---------------------------------------------------------
   * Live waveform animation
   *
   * IMPORTANT:
   * This is handled by an effect instead of making the
   * update function recursively reference itself.
   * ---------------------------------------------------------
   */
  useEffect(() => {
    if (!isRecording) {
      return;
    }

    const updateWaveform = () => {
      const analyser = analyserRef.current;

      if (!analyser) {
        return;
      }

      const data = new Uint8Array(
        analyser.fftSize,
      );

      analyser.getByteTimeDomainData(data);

      const bars: number[] = [];

      const samplesPerBar = Math.max(
        1,
        Math.floor(
          data.length / WAVEFORM_BARS,
        ),
      );

      for (
        let bar = 0;
        bar < WAVEFORM_BARS;
        bar += 1
      ) {
        const start =
          bar * samplesPerBar;

        const end = Math.min(
          start + samplesPerBar,
          data.length,
        );

        let sum = 0;

        for (
          let i = start;
          i < end;
          i += 1
        ) {
          const normalized =
            (data[i] - 128) / 128;

          sum +=
            normalized * normalized;
        }

        const count = Math.max(
          1,
          end - start,
        );

        const rms = Math.sqrt(
          sum / count,
        );

        /*
         * Small baseline keeps the waveform
         * visible during silence.
         */
        const level = Math.min(
          1,
          Math.max(
            0.07,
            rms * 4.5,
          ),
        );

        bars.push(level);
      }

      setWaveform(bars);

      /*
       * requestAnimationFrame is intentionally
       * scheduled here instead of recursively
       * referencing a const callback.
       */
      animationFrameRef.current =
        requestAnimationFrame(updateWaveform);
    };

    /*
     * Start waveform animation.
     */
    animationFrameRef.current =
      requestAnimationFrame(updateWaveform);

    /*
     * Cleanup animation when recording stops.
     */
    return () => {
      if (
        animationFrameRef.current !== null
      ) {
        cancelAnimationFrame(
          animationFrameRef.current,
        );

        animationFrameRef.current = null;
      }
    };
  }, [isRecording]);

  /*
   * ---------------------------------------------------------
   * Recording timer
   * ---------------------------------------------------------
   */
  useEffect(() => {
    if (!isRecording) {
      return;
    }

    const interval = window.setInterval(() => {
      setElapsedSeconds(
        (previous) => previous + 1,
      );
    }, 1000);

    return () => {
      window.clearInterval(interval);
    };
  }, [isRecording]);

  /*
   * ---------------------------------------------------------
   * Stop recording
   * ---------------------------------------------------------
   */
  const stopRecording = useCallback(async () => {
    const recorder =
      mediaRecorderRef.current;

    if (!recorder) {
      return null;
    }

    return new Promise<Blob | null>(
      (resolve) => {
        recorder.onstop = () => {
          const shouldDiscard =
            discardRef.current;

          const blob =
            !shouldDiscard &&
            chunksRef.current.length > 0
              ? new Blob(
                  chunksRef.current,
                  {
                    type:
                      recorder.mimeType ||
                      "audio/webm",
                  },
                )
              : null;

          /*
           * Reset recorder state.
           */
          mediaRecorderRef.current = null;
          chunksRef.current = [];
          discardRef.current = false;

          /*
           * Stop microphone/audio resources.
           */
          cleanupAudio();

          /*
           * Reset UI.
           */
          setIsRecording(false);
          setElapsedSeconds(0);
          setWaveform(
            createIdleWaveform(),
          );

          resolve(blob);
        };

        if (
          recorder.state !== "inactive"
        ) {
          recorder.stop();
        } else {
          cleanupAudio();

          mediaRecorderRef.current = null;
          chunksRef.current = [];

          setIsRecording(false);
          setElapsedSeconds(0);
          setWaveform(
            createIdleWaveform(),
          );

          resolve(null);
        }
      },
    );
  }, [cleanupAudio]);

  /*
   * ---------------------------------------------------------
   * Cancel recording
   *
   * Cancelling discards the recorded audio.
   * ---------------------------------------------------------
   */
  const cancelRecording = useCallback(() => {
    const recorder =
      mediaRecorderRef.current;

    discardRef.current = true;

    if (
      recorder &&
      recorder.state !== "inactive"
    ) {
      recorder.stop();
      return;
    }

    cleanupAudio();

    mediaRecorderRef.current = null;
    chunksRef.current = [];

    setIsRecording(false);
    setElapsedSeconds(0);
    setWaveform(
      createIdleWaveform(),
    );
  }, [cleanupAudio]);

  /*
   * ---------------------------------------------------------
   * Component unmount cleanup
   * ---------------------------------------------------------
   */
  useEffect(() => {
    return () => {
      if (
        animationFrameRef.current !== null
      ) {
        cancelAnimationFrame(
          animationFrameRef.current,
        );

        animationFrameRef.current = null;
      }

      const recorder =
        mediaRecorderRef.current;

      if (
        recorder &&
        recorder.state !== "inactive"
      ) {
        recorder.stop();
      }

      cleanupAudio();
    };
  }, [cleanupAudio]);

  /*
   * ---------------------------------------------------------
   * Public hook API
   * ---------------------------------------------------------
   */
  return {
    isRecording,
    elapsedSeconds,
    waveform,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}