import { useCallback, useEffect, useState } from "react";
import {
  getBackendConnectionState,
  reconnectBackend,
  subscribeBackendConnection,
  type BackendConnectionState,
} from "../lib/api";

export function useBackendConnection() {
  const [state, setState] = useState<BackendConnectionState>(getBackendConnectionState());

  useEffect(() => subscribeBackendConnection(setState), []);

  const reconnect = useCallback(async () => {
    try {
      await reconnectBackend();
    } catch {
      // The shared state already reports the connection failure to the interface.
    }
  }, []);

  return { state, reconnect };
}
