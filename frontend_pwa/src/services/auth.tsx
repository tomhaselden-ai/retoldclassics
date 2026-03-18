import { PropsWithChildren, createContext, useContext, useEffect, useMemo, useState } from "react";

import { AccountProfile, getMe, login as loginRequest } from "./api";

interface AuthContextValue {
  token: string | null;
  account: AccountProfile | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshAccount: () => Promise<void>;
}

const TOKEN_KEY = "psu_access_token";
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [account, setAccount] = useState<AccountProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(token));

  async function refreshAccount() {
    if (!token) {
      setAccount(null);
      return;
    }
    const profile = await getMe(token);
    setAccount(profile);
  }

  useEffect(() => {
    if (!token) {
      setAccount(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    refreshAccount()
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setAccount(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      account,
      loading,
      async login(email: string, password: string) {
        const result = await loginRequest(email, password);
        localStorage.setItem(TOKEN_KEY, result.access_token);
        setToken(result.access_token);
      },
      logout() {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setAccount(null);
      },
      refreshAccount,
    }),
    [account, loading, token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
