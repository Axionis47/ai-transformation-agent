"use client";

import { useState } from "react";
import {
  signInWithPopup,
  signOut,
  type AuthError,
} from "firebase/auth";
import { getFirebaseAuth, googleProvider } from "@/lib/firebase";
import { useAuth } from "@/lib/auth-context";

export default function AuthButton() {
  const { user, loading } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // No Firebase config — render nothing (local dev fallback)
  const hasFirebaseConfig = Boolean(
    process.env.NEXT_PUBLIC_FIREBASE_API_KEY &&
    process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
  );
  if (!hasFirebaseConfig) return null;

  if (loading) {
    return (
      <span className="font-mono text-xs text-ink-faint animate-pulse">
        ...
      </span>
    );
  }

  async function handleSignIn() {
    const firebaseAuth = getFirebaseAuth();
    if (!firebaseAuth) return;
    setBusy(true);
    setError(null);
    try {
      await signInWithPopup(firebaseAuth, googleProvider);
    } catch (err) {
      const authErr = err as AuthError;
      // User closed popup — not an error worth surfacing
      if (authErr.code !== "auth/popup-closed-by-user") {
        setError(`Sign-in failed: ${authErr.code || authErr.message}`);
        console.error("Firebase auth error:", authErr.code, authErr.message);
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleSignOut() {
    const firebaseAuth = getFirebaseAuth();
    if (!firebaseAuth) return;
    setBusy(true);
    try {
      await signOut(firebaseAuth);
    } finally {
      setBusy(false);
    }
  }

  if (user) {
    const initial = (user.displayName || user.email || "?")[0].toUpperCase();
    const displayName = user.displayName || user.email || "Signed in";

    return (
      <div className="flex items-center gap-3">
        {/* Avatar circle */}
        <span
          className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-ink text-cream font-label text-xs font-semibold flex-shrink-0"
          aria-hidden="true"
        >
          {initial}
        </span>
        <span className="font-mono text-xs text-ink-medium hidden sm:inline truncate max-w-32">
          {displayName}
        </span>
        <button
          onClick={handleSignOut}
          disabled={busy}
          className="font-label uppercase tracking-widest text-xs text-ink-light hover:text-red transition-colors disabled:opacity-40"
        >
          {busy ? "..." : "Sign out"}
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      {error && (
        <span className="font-mono text-xs text-red">{error}</span>
      )}
      <button
        onClick={handleSignIn}
        disabled={busy}
        className="font-label uppercase tracking-widest text-xs border border-ink text-ink px-3 py-1 hover:border-red hover:text-red transition-colors disabled:opacity-40"
      >
        {busy ? "..." : "Sign in with Google"}
      </button>
    </div>
  );
}
