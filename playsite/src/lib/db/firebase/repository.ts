// Firebase repository — uncomment when STORAGE_PROVIDER=firebase
//
// import { adminDb } from "./admin";
// import { FieldValue } from "firebase-admin/firestore";
//
// export async function firebaseSave(sessionId: string, command: string, result: any) {
//   await adminDb.collection("history").add({
//     sessionId,
//     command,
//     valid: result.valid,
//     result,
//     timestamp: FieldValue.serverTimestamp(),
//   });
// }
//
// export async function firebaseGet(sessionId: string) {
//   const snap = await adminDb
//     .collection("history")
//     .where("sessionId", "==", sessionId)
//     .orderBy("timestamp", "desc")
//     .limit(50)
//     .get();
//   return snap.docs.map((d) => ({ id: d.id, ...d.data() }));
// }
//
// export async function firebaseClear(sessionId: string) {
//   const snap = await adminDb
//     .collection("history")
//     .where("sessionId", "==", sessionId)
//     .get();
//   const batch = adminDb.batch();
//   snap.docs.forEach((d) => batch.delete(d.ref));
//   await batch.commit();
// }

export {};
