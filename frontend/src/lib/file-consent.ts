export const FILE_NOTICE_VERSION = "files-2026-10-19-v1";
export type FilePurpose = "documents" | "invoice-ocr" | "claim-attachments";
export type ConsentRequest = {purpose: FilePurpose; resolve: (accepted: boolean) => void};

export async function requestFileConsent(purpose: FilePurpose): Promise<boolean> {
  // No consent is persisted in localStorage. Each upload asks before any network request.
  return new Promise(resolve => window.dispatchEvent(new CustomEvent<ConsentRequest>("demo:file-consent", {detail: {purpose, resolve}})));
}
export function fileConsentHeader(purpose: FilePurpose) {
  return {"X-Processing-Consent": `${purpose}:${FILE_NOTICE_VERSION}`};
}
