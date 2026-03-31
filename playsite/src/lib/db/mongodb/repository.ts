// MongoDB repository — uncomment when STORAGE_PROVIDER=mongodb
//
// import { connectDB } from "./client";
// import { CommandHistory } from "./schema";
//
// export async function mongoSave(sessionId: string, command: string, result: any) {
//   await connectDB();
//   await CommandHistory.create({ sessionId, command, valid: result.valid, result });
// }
//
// export async function mongoGet(sessionId: string) {
//   await connectDB();
//   return CommandHistory.find({ sessionId }).sort({ timestamp: -1 }).limit(50).lean();
// }
//
// export async function mongoClear(sessionId: string) {
//   await connectDB();
//   await CommandHistory.deleteMany({ sessionId });
// }

export {};
