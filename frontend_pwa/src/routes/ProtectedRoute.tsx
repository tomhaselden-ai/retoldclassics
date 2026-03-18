import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { LoadingState } from "../components/LoadingState";
import { useAuth } from "../services/auth";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { token, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingState label="Restoring your story portal..." />;
  }

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
}
