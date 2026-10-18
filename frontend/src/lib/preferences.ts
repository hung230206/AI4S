// Preferences are browser-local, never account credentials or server state.
const eventName = "demo:preferences";
const memory = new Map<string, string>();
export function preference(key: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  if (memory.has(key)) return memory.get(key)!;
  try {return localStorage.getItem(key) || fallback;} catch {return fallback;}
}
export function writePreference(key: string, value: string) {
  try {localStorage.setItem(key, value);} catch { /* Use this-tab memory if storage is unavailable. */ }
  memory.set(key, value);
  window.dispatchEvent(new Event(eventName));
}
export function subscribePreferences(listener: () => void) {
  function onStorage(event: StorageEvent) {
    if (event.key) memory.delete(event.key); else memory.clear();
    listener();
  }
  window.addEventListener(eventName, listener);
  window.addEventListener("storage", onStorage);
  return () => {window.removeEventListener(eventName, listener); window.removeEventListener("storage", onStorage);};
}
