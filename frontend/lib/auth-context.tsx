"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import type { User } from "firebase/auth";
import { onAuthStateChanged } from "firebase/auth";
import { getFirebaseAuth } from "@/lib/firebase";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  loading: true,
  refreshToken: async () => {},
});

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshToken = useCallback(async () => {
    if (!user) return;
    try {
      const idToken = await user.getIdToken(/* forceRefresh */ true);
      setToken(idToken);
    } catch {
      setToken(null);
    }
  }, [user]);

  useEffect(() => {
    const firebaseAuth = getFirebaseAuth();

    // No Firebase config — treat as permanently unauthenticated
    if (!firebaseAuth) {
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(firebaseAuth, async (firebaseUser) => {
      setUser(firebaseUser);
      if (firebaseUser) {
        try {
          const idToken = await firebaseUser.getIdToken();
          setToken(idToken);
        } catch {
          setToken(null);
        }
      } else {
        setToken(null);
      }
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  // Refresh token every 50 minutes (Firebase tokens expire after 60 minutes)
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(refreshToken, 50 * 60 * 1000);
    return () => clearInterval(interval);
  }, [user, refreshToken]);

  return (
    <AuthContext.Provider value={{ user, token, loading, refreshToken }}>
      {children}
    </AuthContext.Provider>
  );
}
