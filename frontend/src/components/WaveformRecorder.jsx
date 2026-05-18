import { useEffect, useRef, useState } from "react";

export default function WaveformRecorder({ disabled, onComplete }) {
  const [isRecording, setIsRecording] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState("");
  const [waveform, setWaveform] = useState(Array(20).fill(12));
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const analyserRef = useRef(null);
  const animationRef = useRef(0);
  const timerRef = useRef(0);
  const audioContextRef = useRef(null);
  const stopFallbackRef = useRef(0);

  useEffect(() => () => cleanup(), []);

  const cleanup = () => {
    window.clearInterval(timerRef.current);
    window.cancelAnimationFrame(animationRef.current);
    window.clearTimeout(stopFallbackRef.current);
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    analyserRef.current = null;
    mediaRecorderRef.current = null;
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {});
    }
    audioContextRef.current = null;
    setIsStopping(false);
  };

  const drawWaveform = () => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);
    const bars = Array.from({ length: 20 }, (_, index) => {
      const sample = data[index * 2] || 0;
      return Math.max(8, Math.round(sample / 4));
    });
    setWaveform(bars);
    animationRef.current = window.requestAnimationFrame(drawWaveform);
  };

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || isStopping) return;
    setIsStopping(true);
    setIsRecording(false);
    window.clearInterval(timerRef.current);
    window.cancelAnimationFrame(animationRef.current);

    try {
      if (recorder.state === "recording") {
        recorder.stop();
      }
    } catch (err) {
      setError("VoiceTrace could not stop that recording cleanly. Please try again.");
      cleanup();
      return;
    }

    window.setTimeout(() => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
    }, 50);

    stopFallbackRef.current = window.setTimeout(() => {
      if (mediaRecorderRef.current) {
        setError("VoiceTrace is taking longer than expected to finish the recording. Please try again.");
        cleanup();
      }
    }, 4000);
  };

  const startRecording = async () => {
    try {
      setError("");
      setElapsed(0);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const audioContext = new window.AudioContext();
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      analyserRef.current = analyser;

      const mimeTypes = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
      const supportedMimeType =
        mimeTypes.find((mimeType) => window.MediaRecorder?.isTypeSupported?.(mimeType)) ?? "";
      const recorder = supportedMimeType
        ? new MediaRecorder(stream, { mimeType: supportedMimeType })
        : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      recorder.onerror = () => {
        setError("VoiceTrace could not finalize that recording. Please try again.");
        cleanup();
      };
      recorder.onstop = async () => {
        try {
          window.clearTimeout(stopFallbackRef.current);
          const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
          if (!blob.size) {
            setError("VoiceTrace captured an empty recording. Please try again and speak for a few seconds.");
            return;
          }
          await onComplete(blob);
          setElapsed(0);
        } catch (err) {
          setError("VoiceTrace could not start the upload for that recording. Please try again.");
        } finally {
          cleanup();
        }
      };
      recorder.start(250);
      setIsRecording(true);
      drawWaveform();

      timerRef.current = window.setInterval(() => {
        setElapsed((value) => {
          const next = value + 1;
          if (next >= 120) stopRecording();
          return next;
        });
      }, 1000);
    } catch (err) {
      setError("Microphone access is needed to record a diary entry.");
      cleanup();
    }
  };

  return (
    <div className="glass-card p-8 text-center">
      <div className="mx-auto flex max-w-md flex-col items-center gap-6">
        <button
          className={`h-36 w-36 rounded-full text-lg font-semibold text-white shadow-calm transition ${
            isRecording ? "bg-teal-700" : "bg-ink"
          } disabled:cursor-not-allowed disabled:bg-slate-400`}
          disabled={disabled || isStopping}
          onClick={isRecording ? stopRecording : startRecording}
          type="button"
        >
          {isStopping ? "Finishing..." : isRecording ? "Stop" : "Start Recording"}
        </button>
        <div className="flex h-24 items-end gap-1">
          {waveform.map((bar, index) => (
            <span
              key={`${bar}-${index}`}
              className="w-3 rounded-full bg-teal-400 transition-all"
              style={{ height: `${bar * 2}px` }}
            />
          ))}
        </div>
        <div className="space-y-2">
          <p className="text-xl font-semibold text-ink">
            {isStopping ? "Finishing your recording..." : isRecording ? "Recording your diary entry..." : "Ready when you are"}
          </p>
          <p className="text-slate-600">Elapsed time: {Math.floor(elapsed / 60)}:{`${elapsed % 60}`.padStart(2, "0")}</p>
          <p className="text-slate-500">Recording stops automatically at 2:00.</p>
        </div>
        {error && <p className="text-rose-700">{error}</p>}
      </div>
    </div>
  );
}
