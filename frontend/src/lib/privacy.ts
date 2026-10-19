import type {Locale} from "./i18n";
import type {FilePurpose} from "./file-consent";
export const AI_PRIVACY_NOTICE_VERSION = "ai-privacy-2026-10-19-v2";

export type AiPermission = {enabled: boolean; revision: number; notice_version: string; scopes: string[]; data_mode: "DEMO_ONLY" | "PAID_PRIVATE"; granted_at: string | null; expires_at: string | null; allowed_scopes: string[]};
const copy = {
  vi: {
    noticeChanged: "Thông báo quyền đã thay đổi. Tải lại trang trước khi cấp quyền mới.",
    title: "Cho phép dùng Gemini?", manage: "Xem quyền Gemini", enable: "Đồng ý", revoke: "Thu hồi quyền Gemini", cancel: "Không đồng ý", details: "Xem chi tiết quyền và cách xử lý dữ liệu", close: "Đóng", saving: "Đang lưu…",
    off: "Chưa cho phép gửi tới Google Gemini.", on: "Đã cho phép trong phiên này, tối đa 1 giờ. Có thể thu hồi bất cứ lúc nào.",
    purpose: "Để trả lời bằng Gemini, bạn cho phép gửi câu hỏi, tối đa 3 lượt Gemini gần nhất trong tab và tối đa 3 đoạn tài liệu mẫu/công khai liên quan tới Google. Không gửi dữ liệu tài chính, hợp đồng cá nhân hay hồ sơ bồi thường. Quyền có hiệu lực trong phiên này, tối đa 1 giờ; có thể thu hồi. Không đồng ý thì tiếp tục tra cứu trực tiếp.",
    demo: "Bản demo dùng chế độ không gửi dữ liệu tài khoản cá nhân. Với Gemini miễn phí, Google có thể dùng nội dung để cải thiện mô hình và có người đánh giá. Chỉ dùng câu hỏi và tài liệu mẫu/công khai không chứa thông tin cá nhân.",
    paid: "Google có thể lưu nội dung có thời hạn để kiểm tra an toàn theo điều khoản dịch vụ. Popup này chỉ cấp quyền cho câu hỏi, hội thoại Gemini và tài liệu mẫu/công khai, không cấp quyền dữ liệu tài khoản cá nhân.",
    history: "Gửi tối đa 3 lượt Gemini gần nhất trong tab này", documents: "Gửi tối đa 3 đoạn tài liệu liên quan", finance: "Gửi tóm tắt ngân sách và hóa đơn", insurance: "Gửi tóm tắt hợp đồng đã đối chiếu",
    docDemo: "Chỉ tài liệu gắn nhãn mẫu tự soạn hoặc tham khảo công khai; tài liệu cá nhân bị loại ở máy chủ.",
    excluded: "Luôn loại trừ: mật khẩu, cookie, mã vận hành, tệp gốc, chứng từ và mô tả bệnh trong hồ sơ bồi thường. Không cấp quyền thanh toán, chỉnh sửa hay gửi hồ sơ cho AI.",
    ack: "Tôi đã đọc thông báo và tự nguyện cho phép Google Gemini xử lý câu hỏi cùng các nhóm đã chọn để trả lời.", adult: "Tôi xác nhận từ 18 tuổi trở lên.", nonSensitive: "Tôi sẽ chỉ gửi dữ liệu mẫu/công khai hoặc đã ẩn danh, không có dữ liệu cá nhân, sức khỏe, định danh hay bí mật.",
    revokeNote: "Thu hồi chặn các yêu cầu mới. Không thể rút lại nội dung đã gửi hoặc hủy yêu cầu đang xử lý tại Google. Xóa chat chỉ xóa nội dung trong tab, không xóa bản phía Google.",
    policy: "Thông báo quyền riêng tư", terms: "Điều khoản dữ liệu Gemini", scope: "Phạm vi đã được ấn định cho chức năng này; không cần chọn từng quyền.",
    preview: "Xem dữ liệu sẽ gửi", previewTitle: "Xem trước dữ liệu cho Gemini", previewNote: "Chưa gửi tới Google. Đây là dữ liệu tại thời điểm xem; sẽ được kiểm tra quyền lại khi gửi.",
    keyboard: "Enter để gửi · Shift+Enter xuống dòng", upload: "Tệp bạn chọn chỉ được tải khi bấm nút tải lên. Máy chủ lưu và đọc/OCR nội bộ; không gửi tệp gốc tới Gemini. Chỉ chọn tệp bạn có quyền sử dụng. Ở tài khoản mẫu dùng chung, chỉ tải dữ liệu giả lập; tài liệu riêng cần tài khoản cá nhân.",
    allSessions: "Đăng xuất trên mọi thiết bị", questionOnly: "Chỉ câu hỏi; chưa cấp thêm nhóm ngữ cảnh.",
  },
  en: {
    noticeChanged: "The permission notice has changed. Reload before granting new permission.",
    title: "Allow Gemini?", manage: "View Gemini access", enable: "Agree", revoke: "Revoke Gemini access", cancel: "Disagree", details: "Permission and data processing details", close: "Close", saving: "Saving…",
    off: "No permission to send to Google Gemini.", on: "Allowed for this session, for up to 1 hour. Revoke at any time.",
    purpose: "To answer with Gemini, allow sending your question, up to 3 recent Gemini turns in this tab and up to 3 relevant sample/public document excerpts to Google. Financial records, personal policies and claim files are excluded. Access lasts for this session, up to 1 hour; revoke at any time. Disagree to continue direct lookup.",
    demo: "Demo mode excludes personal account data. With unpaid Gemini, Google may use content to improve models and human reviewers may read it. Use only non-personal sample/public questions and documents.",
    paid: "Google may temporarily retain content for safety checks under its terms. This popup permits only questions, Gemini conversation and sample/public excerpts, not personal account records.",
    history: "Send up to 3 recent Gemini turns in this tab", documents: "Send up to 3 relevant document excerpts", finance: "Send budget and invoice summaries", insurance: "Send reviewed policy summaries",
    docDemo: "Only self-authored sample or public-reference documents; personal documents are excluded on the server.",
    excluded: "Always excluded: passwords, cookies, operator codes, original files, claim attachments and medical descriptions. AI has no payment, editing or claim-submission permissions.",
    ack: "I have read this notice and voluntarily allow Google Gemini to process my question and selected groups to answer it.", adult: "I confirm I am at least 18 years old.", nonSensitive: "I will send only sample/public or anonymised content, with no personal, health, identity or secret information.",
    revokeNote: "Revoking blocks new requests. It cannot recall content already sent or cancel a request Google is processing. Clearing chat removes this tab's content, not Google's copies.",
    policy: "Privacy notice", terms: "Gemini data terms", scope: "Permissions are predetermined for this feature; there are no individual permission choices.",
    preview: "Preview data to send", previewTitle: "Gemini data preview", previewNote: "Not sent to Google. This is a snapshot at preview time; permissions are checked again when you send.", keyboard: "Enter to send · Shift+Enter for a new line",
    upload: "The selected file is uploaded only when you press upload. The server stores and reads/OCRs it locally; original bytes are never sent to Gemini. Upload only files you may use. In the shared sample account, use fictional files only; private documents need a personal account.",
    allSessions: "Sign out on all devices", questionOnly: "Question only; no extra context groups allowed.",
  },
  zh: {
    noticeChanged: "授权通知已更改，请刷新页面后重新授权。",
    title: "允许使用 Gemini？", manage: "查看 Gemini 权限", enable: "同意", revoke: "撤销 Gemini 权限", cancel: "不同意", details: "权限及数据处理详情", close: "关闭", saving: "正在保存…",
    off: "尚未允许向 Google Gemini 发送数据。", on: "仅本次登录有效，最长1小时，可随时撤销。",
    purpose: "使用 Gemini 回答时，允许向 Google 发送问题、本标签页最近最多3轮 Gemini 对话及最多3段相关示例或公开文档。不发送个人财务、保单或理赔档案。授权仅本次登录有效，最长1小时，可随时撤销。不同意则继续直接检索。",
    demo: "演示模式不发送个人账户数据。免费 Gemini 可能使用内容改进模型，并由人工审核。请仅使用不含个人信息的示例或公开问题及文档。",
    paid: "Google 可能按条款临时保留内容进行安全检查。本弹窗仅允许问题、Gemini 对话及示例或公开文档，不授权个人账户数据。",
    history: "发送本标签页最近最多3轮 Gemini 对话", documents: "发送最多3段相关文档摘录", finance: "发送预算和账单摘要", insurance: "发送已核对的保单摘要", docDemo: "仅限自编示例或公开参考文档；服务器排除个人文档。",
    excluded: "始终排除密码、Cookie、操作员代码、原始文件、理赔附件及病情描述。AI 无支付、修改或提交理赔的权限。",
    ack: "我已阅读通知，并自愿允许 Google Gemini 处理问题及所选类别以生成回答。", adult: "我确认已年满18周岁。", nonSensitive: "我仅发送示例、公开或匿名内容，不含个人、健康、身份信息或秘密。",
    revokeNote: "撤销会阻止新请求，无法撤回已发送内容或取消 Google 正在处理的请求。清空聊天仅清除本标签页内容，不删除 Google 的副本。",
    policy: "隐私通知", terms: "Gemini 数据条款", scope: "此功能的权限范围已固定，无需逐项选择。", preview: "预览将发送的数据", previewTitle: "Gemini 数据预览", previewNote: "尚未发送给 Google。此为预览时的数据，发送时将再次检查权限。", keyboard: "Enter 发送 · Shift+Enter 换行",
    upload: "仅点击上传后才发送所选文件。服务器在本地存储和读取/OCR，原始文件不会发送给 Gemini。请仅上传有权使用的文件。共享示例账户仅使用虚构文件；私人文档请使用个人账户。", allSessions: "退出所有设备", questionOnly: "仅问题，未授权附加上下文。",
  },
};
export function privacyText(locale: Locale) {return copy[locale];}

export function fileNotice(locale: Locale, purpose: FilePurpose) {
  const notices = {
    vi: {
      documents: {title: "Cho phép xử lý tài liệu?", summary: "Demo được tải lên, lưu tệp bạn chọn và đọc/OCR nội dung trên máy chủ để tra cứu, trích dẫn và đối chiếu hợp đồng."},
      "invoice-ocr": {title: "Cho phép đọc hóa đơn?", summary: "Demo được tải lên, lưu tệp bạn chọn và đọc/OCR trên máy chủ để gợi ý mã hóa đơn, số tiền, bên nhận và hạn thanh toán. Bạn đối chiếu trước khi lưu hóa đơn."},
      "claim-attachments": {title: "Cho phép lưu chứng từ hồ sơ?", summary: "Demo được lưu tệp bạn chọn trong hồ sơ bồi thường này để bạn đối chiếu, tải lại và xuất bộ hồ sơ. Không gửi tới công ty bảo hiểm hay Gemini."},
    },
    en: {
      documents: {title: "Allow document processing?", summary: "Allow Demo to upload, store and read/OCR the selected file on the application server for lookup, citations and policy review."},
      "invoice-ocr": {title: "Allow invoice reading?", summary: "Allow Demo to upload, store and read/OCR the selected file on the application server to suggest invoice fields. You review them before saving the invoice."},
      "claim-attachments": {title: "Allow claim attachment storage?", summary: "Allow Demo to store the selected file in this claim for your review, download and export. It is not sent to an insurer or Gemini."},
    },
    zh: {
      documents: {title: "允许处理文档？", summary: "允许 Demo 上传、存储并在应用服务器读取/OCR所选文件，用于检索、引用和保单核对。"},
      "invoice-ocr": {title: "允许读取账单？", summary: "允许 Demo 上传、存储并在应用服务器读取/OCR所选文件，以建议账单字段。保存前由您核对。"},
      "claim-attachments": {title: "允许保存理赔附件？", summary: "允许 Demo 将所选文件保存到本理赔档案，供您核对、下载及导出。不会发送至保险公司或 Gemini。"},
    },
  };
  const limit = locale === "vi" ? "Chỉ áp dụng cho tệp này. Không gửi tệp gốc tới Gemini, không truy cập tệp khác. Từ chối sẽ hủy tải lên. Chỉ dùng tệp mẫu hoặc đã ẩn danh mà bạn có quyền sử dụng." : locale === "zh" ? "仅限本次所选文件，不向 Gemini 发送原始文件，也不访问其他文件。拒绝即取消上传。仅使用有权使用的示例或匿名文件。" : "Applies only to this selected file. No original bytes go to Gemini and no other files are accessed. Disagree cancels the upload. Use only sample or anonymised files you may use.";
  return {...notices[locale][purpose], limit};
}
