// Notification utility for Pal
import { invoke } from "@tauri-apps/api/core";

// Send a native OS notification
export async function sendNotification(title: string, body: string): Promise<void> {
  try {
    await invoke("send_notification", { title, body });
  } catch (err) {
    console.warn("Could not send notification:", err);
  }
}
