"use client";
import Link from "next/link";
import {useI18n} from "@/components/i18n-provider";
import {privacyText, fileNotice, AI_PRIVACY_NOTICE_VERSION} from "@/lib/privacy";

export default function PrivacyPage() {
  const {locale} = useI18n(); const t = privacyText(locale);
  const sections = locale === "vi" ? [
    ["Dữ liệu và mục đích", "Demo lưu email, tên hiển thị và mật khẩu đã băm để đăng nhập; hóa đơn, sổ thu chi, tài liệu và hồ sơ do bạn nhập để cung cấp chức năng bạn yêu cầu. OCR và tra cứu trực tiếp chạy trên máy chủ ứng dụng. Không có quảng cáo hay phân tích hành vi bên thứ ba."],
    ["Ai có thể xử lý dữ liệu?", "Ứng dụng và cơ sở dữ liệu được lưu tại Render; người quản trị hạ tầng có khả năng truy cập dữ liệu. Gemini của Google là bên nhận tùy chọn, chỉ sau khi bạn cho phép trong từng phiên. Frankfurter nhận yêu cầu tỷ giá chung, không nhận hồ sơ cá nhân. Không có kết nối ngân hàng hoặc nhà bảo hiểm."],
    ["Quyền tùy chọn cho Gemini", t.purpose + " " + t.demo + " " + t.scope + " " + t.excluded],
    ["Lưu trữ và thu hồi", "Hội thoại chỉ giữ trong bộ nhớ tab; ứng dụng không lưu câu hỏi/câu trả lời vào DB hoặc nhật ký. Quyền AI hết hạn sau tối đa 1 giờ hoặc khi phiên đăng nhập hết hiệu lực; nhật ký lưu loại quyền, phiên bản thông báo, thời gian và lần gửi, không lưu nội dung. " + t.revokeNote],
    ["Tệp và quyền kiểm soát", "Bạn có thể xem, tải lại và xóa tài liệu chưa được hợp đồng/hồ sơ tham chiếu; tệp hồ sơ nháp có thể gỡ, nhật ký giữ mã băm. Tài liệu đã được tham chiếu hoặc hồ sơ khóa được giữ để đối chiếu. Dữ liệu tài khoản hiện được giữ đến khi xóa theo chức năng được hỗ trợ hoặc quản trị viên xử lý. Chưa có chức năng tự xóa toàn bộ tài khoản, lịch xóa tự động hay xóa các bản sao lưu theo yêu cầu."],
    ["Cookie và quyền thiết bị", "Cookie đăng nhập HttpOnly là cần thiết cho phiên. Ngôn ngữ, sáng/tối và hướng dẫn được lưu trong trình duyệt. Không xin camera, micro, vị trí, danh bạ hay quyền đọc toàn bộ ổ đĩa. Chọn tệp chỉ cho phép xử lý tệp bạn chọn sau khi bấm tải lên; không cấp quyền AI đọc toàn bộ tài khoản."],
    ["Giới hạn và liên hệ", "Đây là MVP của team dự thi, chưa phải chứng nhận tuân thủ pháp luật hay kiểm toán độc lập. Bộ lọc dữ liệu nhạy cảm chỉ là lớp hỗ trợ, không bảo đảm ẩn danh. Chỉ dùng dữ liệu giả lập/đã ẩn danh khi thử. Vấn đề bảo mật hoặc yêu cầu xóa dữ liệu: liên hệ team quản trị qua kho mã nguồn, không đăng dữ liệu cá nhân trong issue công khai."],
  ] : locale === "zh" ? [
    ["数据及目的", "应用存储登录邮箱、昵称、密码哈希及您输入的账单、财务记录、文档和理赔准备数据。OCR 和直接检索在应用服务器运行，无第三方广告或行为分析。"],
    ["处理方", "Render 托管应用和数据库，基础设施管理员可能访问数据。Google Gemini 是需单独授权的可选接收方。Frankfurter 仅接收通用汇率查询，不接收个人档案。没有银行或保险公司连接。"],
    [t.title, t.purpose + " " + t.demo + " " + t.scope + " " + t.excluded],
    ["保留与撤销", "对话仅存在标签页内存中，不写入应用数据库或日志。授权最长1小时，并随登录失效而失效。日志记录权限、版本、时间和发送事件，不记录问题或回答。" + t.revokeNote],
    ["文件控制", "可以下载及删除未被保单或历史理赔引用的文档，移除草稿附件（日志保留哈希）。已引用文件保留用于核对。其他数据保留至受支持的删除操作或管理员处理。目前不支持自行删除整个账户、自动清理或按需删除备份。"],
    ["Cookie 和设备权限", "登录使用必要的 HttpOnly Cookie，浏览器保存语言、主题和引导偏好。不申请摄像头、麦克风、位置、通讯录或整个磁盘权限。选择文件后仅在点击上传时处理该文件。"],
    ["限制与联系", "这是参赛 MVP，并非法律合规认证或独立审计。敏感信息检测不能保证匿名。测试仅使用虚构或匿名数据。请通过源码仓库联系项目团队，勿在公开 issue 发布个人数据。"],
  ] : [
    ["Data and purposes", "Demo stores login email, display name, a password hash, and the invoices, finance records, documents and claim-preparation data you enter to provide requested features. OCR and direct lookup run on the application server. There are no third-party ads or behavioural analytics."],
    ["Recipients", "Render hosts the app and database; infrastructure administrators may access data. Google Gemini is an optional recipient requiring separate permission. Frankfurter receives generic FX queries, not personal records. There is no bank or insurer connection."],
    [t.title, t.purpose + " " + t.demo + " " + t.scope + " " + t.excluded],
    ["Retention and withdrawal", "Conversation exists only in tab memory; questions and replies are not stored in the app database or logs. AI permission lasts up to 1 hour and requires a valid login. Audit records contain permission scopes, notice version, times and dispatch events, not chat content. " + t.revokeNote],
    ["File controls", "Download or delete documents not referenced by policies or historical claims; remove draft attachments (their hashes remain in the journal). Referenced sources are retained for evidence. Other account data remains until supported deletion or administrator action. Full self-service account erasure, automatic retention cleanup and requested backup erasure are not implemented."],
    ["Cookies and device access", "A necessary HttpOnly cookie maintains login. Language, theme and guide preferences are stored in your browser. We request no camera, microphone, location, contacts or full-disk permissions. Selecting a file only enables processing that file after you press upload."],
    ["Limits and contact", "This competition MVP has no legal compliance certification or independent audit. Sensitive-data detection cannot guarantee anonymity. Test with fictional or anonymised data. Contact the project team through the source repository; do not post personal information in public issues."],
  ];
  return <main className="privacy-page"><Link className="text-link" href="/account">← Demo</Link><h1>{t.policy}</h1><p className="small muted">19/10/2026 · {AI_PRIVACY_NOTICE_VERSION}</p>{sections.map(([title, body]) => <section id={title === t.title || title === "Quyền tùy chọn cho Gemini" ? "gemini" : undefined} key={title}><h2>{title}</h2><p>{body}</p></section>)}{(["documents", "invoice-ocr", "claim-attachments", "rag-corpus", "rag-publish"] as const).map(purpose => {const notice = fileNotice(locale, purpose); return <section id={purpose} key={purpose}><h2>{notice.title}</h2><p>{notice.summary} {notice.limit}</p><p>{t.upload}</p><p>{sections[4][1]}</p></section>;})}<p><a className="text-link" href="https://ai.google.dev/gemini-api/terms" target="_blank" rel="noreferrer">{t.terms} ↗</a> · <a className="text-link" href="https://github.com/hung230206/AI4S" target="_blank" rel="noreferrer">GitHub</a></p></main>;
}
