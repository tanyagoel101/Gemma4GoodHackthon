import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import App from "./App";

vi.mock("./hooks/useHealthStatus", () => ({
  useHealthStatus: () => ({
    loading: false,
    health: {
      status: "degraded",
      message: "Run ollama pull gemma4",
    },
  }),
}));

vi.mock("./api/client", () => ({
  getClinicianPatients: () => Promise.resolve([]),
}));

describe("App", () => {
  it("shows the setup modal when health is degraded", () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByText("Local AI Setup Needed")).toBeInTheDocument();
  });
});
