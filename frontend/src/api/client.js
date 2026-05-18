import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 240000,
});

export const getHealth = async () => (await client.get("/health")).data;
export const getPatients = async () => (await client.get("/api/patients")).data;
export const createPatient = async (payload) => (await client.post("/api/patients", payload)).data;
export const getSessions = async (patientId) => (await client.get(`/api/patients/${patientId}/sessions`)).data;
export const getBaseline = async (patientId) => (await client.get(`/api/patients/${patientId}/baseline`)).data;
export const getWeeklySummary = async (patientId) =>
  (await client.get(`/api/patients/${patientId}/weekly-summary`)).data;
export const getLifeEvents = async (patientId) => (await client.get(`/api/patients/${patientId}/events`)).data;
export const createLifeEvent = async (patientId, payload) =>
  (await client.post(`/api/patients/${patientId}/events`, payload)).data;
export const getCorrelations = async (patientId) =>
  (await client.get(`/api/patients/${patientId}/correlations`)).data;
export const getDailyPrompt = async (patientId, category) =>
  (await client.get(`/api/prompts/daily/${patientId}`, { params: category ? { category } : {} })).data;
export const getClinicianPatients = async () => (await client.get("/api/clinician/patients")).data;
export const getBrief = async (patientId) =>
  (await client.get(`/api/clinician/patients/${patientId}/brief`)).data;
export const getReferral = async (patientId, referringGp) =>
  (await client.get(`/api/clinician/patients/${patientId}/referral`, { params: { referring_gp: referringGp } }))
    .data;
export const downloadPdf = async (patientId) =>
  (await client.get(`/api/reports/${patientId}/pdf`, { responseType: "blob" })).data;
export const uploadRecording = async (
  patientId,
  audioBlob,
  filename = "recording.webm",
  { promptText = "", promptCategory = "freeform" } = {},
) => {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 240000);

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/recordings/upload-blob?patient_id=${encodeURIComponent(patientId)}&filename=${encodeURIComponent(filename)}&prompt_text=${encodeURIComponent(promptText)}&prompt_category=${encodeURIComponent(promptCategory)}`,
      {
      method: "POST",
      body: audioBlob,
      headers: {
        "Content-Type": audioBlob.type || "application/octet-stream",
      },
      signal: controller.signal,
    },
    );

    if (!response.ok) {
      let detail = "VoiceTrace could not upload the recording.";
      try {
        const payload = await response.json();
        detail = payload?.detail ?? detail;
      } catch (error) {
        // Ignore JSON parsing errors and keep the fallback message.
      }
      const requestError = new Error(detail);
      requestError.response = { data: { detail } };
      throw requestError;
    }

    return await response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      const timeoutError = new Error("The local analysis took too long to respond. Please try a shorter recording first to warm up the models.");
      timeoutError.code = "ECONNABORTED";
      throw timeoutError;
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
};
