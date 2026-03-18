import { ReactNode, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { LoadingState } from "../components/LoadingState";
import { type ParentPinStatusResponse } from "../services/api";
import { useAuth } from "../services/auth";
import { loadParentPinStatus } from "../services/parentPin";


export function ParentProtectedRoute({ children }: { children: ReactNode }) {
  const { token, account, loading } = useAuth();
  const location = useLocation();
  const [status, setStatus] = useState<ParentPinStatusResponse | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);

  useEffect(() => {
    if (!token || !account) {
      return;
    }

    let cancelled = false;
    setStatusLoading(true);

    loadParentPinStatus(token, account.account_id)
      .then((payload) => {
        if (!cancelled) {
          setStatus(payload);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStatus({
            pin_enabled: false,
            verified: false,
            locked_until: null,
            attempts_remaining: 0,
            session_expires_at: null,
          });
        }
      })
      .finally(() => {
        if (!cancelled) {
          setStatusLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [account, token]);

  if (loading) {
    return <LoadingState label="Restoring your story portal..." />;
  }

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (statusLoading) {
    return <LoadingState label="Unlocking parent controls..." />;
  }

  if (!status?.pin_enabled || !status.verified) {
    return <Navigate to="/parent/pin" replace state={{ from: location.pathname }} />;
  }

  return children;
}
