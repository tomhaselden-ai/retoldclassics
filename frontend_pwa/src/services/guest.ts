import { ApiError, GuestLimitsResponse, startGuestSession } from "./api";


const GUEST_SESSION_TOKEN_KEY = "psu_guest_session_token";


export function getStoredGuestSessionToken(): string | null {
  return localStorage.getItem(GUEST_SESSION_TOKEN_KEY);
}


export function clearStoredGuestSessionToken(): void {
  localStorage.removeItem(GUEST_SESSION_TOKEN_KEY);
}


export async function ensureGuestSession(): Promise<GuestLimitsResponse> {
  const existingSessionToken = getStoredGuestSessionToken();

  try {
    const response = await startGuestSession(existingSessionToken);
    localStorage.setItem(GUEST_SESSION_TOKEN_KEY, response.session_token);
    return response;
  } catch (error) {
    if (error instanceof ApiError && (error.code === "guest_session_required" || error.code === "guest_session_expired")) {
      clearStoredGuestSessionToken();
      const response = await startGuestSession(null);
      localStorage.setItem(GUEST_SESSION_TOKEN_KEY, response.session_token);
      return response;
    }
    throw error;
  }
}
