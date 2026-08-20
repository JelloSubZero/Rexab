"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { ReactNode } from "react";
import { api, setAuthToken } from "@/lib/api";
import type { User } from "@/types/api";

const TOKEN_KEY = "rexab_token";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    firstName: string,
  ) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);

    if (!token) {
      // localStorage is only available client-side, so this has to
      // run in an effect rather than during render (SSR-safe).
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsLoading(false);
      return;
    }

    setAuthToken(token);

    api.auth
      .me()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setAuthToken(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const applySession = useCallback(
    (token: string, sessionUser: User) => {
      localStorage.setItem(TOKEN_KEY, token);
      setAuthToken(token);
      setUser(sessionUser);
    },
    [],
  );

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await api.auth.login({ email, password });
      applySession(response.access_token, response.user);
    },
    [applySession],
  );

  const register = useCallback(
    async (email: string, password: string, firstName: string) => {
      const response = await api.auth.register({
        email,
        password,
        first_name: firstName,
      });
      applySession(response.access_token, response.user);
    },
    [applySession],
  );

  const logout = useCallback(() => {
    api.auth.logout().catch(() => {});
    localStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isLoading, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
