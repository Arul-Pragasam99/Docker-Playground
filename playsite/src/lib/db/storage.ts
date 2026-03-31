// Storage abstraction — swap between local, mongodb, firebase
// Set STORAGE_PROVIDER in .env.local

const PROVIDER = process.env.STORAGE_PROVIDER || "local";

// ─── Local in-memory store ────────────────────────────────────────────────────
const memoryStore: Record<string, any[]> = {};

async function localSave(sessionId: string, command: string, result: any) {
  if (!memoryStore[sessionId]) memoryStore[sessionId] = [];
  memoryStore[sessionId].unshift({
    id: Date.now().toString(),
    command,
    valid: result.valid,
    timestamp: new Date().toISOString(),
    result,
  });
  // Keep last 50
  if (memoryStore[sessionId].length > 50) memoryStore[sessionId].pop();
}

async function localGet(sessionId: string) {
  return memoryStore[sessionId] || [];
}

async function localClear(sessionId: string) {
  delete memoryStore[sessionId];
}

// ─── MongoDB (uncomment to enable) ───────────────────────────────────────────
// import { mongoSave, mongoGet, mongoClear } from "./mongodb/repository";

// ─── Firebase (uncomment to enable) ──────────────────────────────────────────
// import { firebaseSave, firebaseGet, firebaseClear } from "./firebase/repository";

// ─── Public API ───────────────────────────────────────────────────────────────
export async function saveCommand(sessionId: string, command: string, result: any) {
  if (PROVIDER === "mongodb") {
    // return mongoSave(sessionId, command, result);
    throw new Error("MongoDB not configured. Uncomment mongodb imports in storage.ts");
  }
  if (PROVIDER === "firebase") {
    // return firebaseSave(sessionId, command, result);
    throw new Error("Firebase not configured. Uncomment firebase imports in storage.ts");
  }
  return localSave(sessionId, command, result);
}

export async function getHistory(sessionId: string) {
  if (PROVIDER === "mongodb") {
    // return mongoGet(sessionId);
    throw new Error("MongoDB not configured.");
  }
  if (PROVIDER === "firebase") {
    // return firebaseGet(sessionId);
    throw new Error("Firebase not configured.");
  }
  return localGet(sessionId);
}

export async function clearHistory(sessionId: string) {
  if (PROVIDER === "mongodb") {
    // return mongoClear(sessionId);
    throw new Error("MongoDB not configured.");
  }
  if (PROVIDER === "firebase") {
    // return firebaseClear(sessionId);
    throw new Error("Firebase not configured.");
  }
  return localClear(sessionId);
}
