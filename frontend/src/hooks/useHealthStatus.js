import { useEffect, useState } from "react";
import { getHealth } from "../api/client";

export function useHealthStatus() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const data = await getHealth();
        if (mounted) setHealth(data);
      } catch (err) {
        if (mounted) setError(err);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    const interval = window.setInterval(load, 10000);
    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  return { health, loading, error };
}
