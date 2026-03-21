import { type FirebaseApp, initializeApp, getApps } from "firebase/app";
import { type Auth, getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "plotpointe",
};

let _app: FirebaseApp | null = null;
let _auth: Auth | null = null;

/**
 * Returns the Firebase Auth instance, or null if no API key is configured.
 * Initialization is deferred so that missing env vars during static generation
 * do not throw auth/invalid-api-key.
 */
export function getFirebaseAuth(): Auth | null {
  if (!firebaseConfig.apiKey) return null;
  if (!_auth) {
    _app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
    _auth = getAuth(_app);
  }
  return _auth;
}

export const googleProvider = new GoogleAuthProvider();
