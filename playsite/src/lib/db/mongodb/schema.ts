// MongoDB schema — uncomment when STORAGE_PROVIDER=mongodb
//
// import mongoose, { Schema, Document } from "mongoose";
//
// export interface ICommandHistory extends Document {
//   sessionId: string;
//   command: string;
//   valid: boolean;
//   result: Record<string, any>;
//   timestamp: Date;
// }
//
// const CommandHistorySchema = new Schema<ICommandHistory>({
//   sessionId: { type: String, required: true, index: true },
//   command: { type: String, required: true },
//   valid: { type: Boolean, required: true },
//   result: { type: Schema.Types.Mixed },
//   timestamp: { type: Date, default: Date.now },
// });
//
// export const CommandHistory =
//   mongoose.models.CommandHistory ||
//   mongoose.model<ICommandHistory>("CommandHistory", CommandHistorySchema);

export {};
