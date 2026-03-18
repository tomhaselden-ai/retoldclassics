import { ApiError, getParentPinStatus, type ParentPinStatusResponse } from "./api";


function buildStorageKey(accountId: number): string {
  return `psu_parent_pin_session_${accountId}`;
}


export function getStoredParentPinSessionToken(accountId: number): string | null {
  return localStorage.getItem(buildStorageKey(accountId));
}


export function storeParentPinSessionToken(accountId: number, sessionToken: string): void {
  localStorage.setItem(buildStorageKey(accountId), sessionToken);
}


export function clearStoredParentPinSessionToken(accountId: number): void {
  localStorage.removeItem(buildStorageKey(accountId));
}


export async function loadParentPinStatus(token: string, accountId: number): Promise<ParentPinStatusResponse> {
  const sessionToken = getStoredParentPinSessionToken(accountId);

  try {
    const status = await getParentPinStatus(token, sessionToken);
    if (!status.verified && sessionToken) {
      clearStoredParentPinSessionToken(accountId);
    }
    return status;
  } catch (error) {
    if (error instanceof ApiError && (error.code === "parent_pin_session_required" || error.code === "request_failed")) {
      clearStoredParentPinSessionToken(accountId);
      return getParentPinStatus(token, null);
    }
    throw error;
  }
}
