"use client";
import Link from "next/link";
import {useI18n} from "@/components/i18n-provider";
import {privacyText, fileNotice} from "@/lib/privacy";

export default function PrivacyPage() {
  const {locale} = useI18n(); const t = privacyText(locale);
  const sections = {
    vi: [
      ["data", "Thông tin được sử dụng", "Demo lưu thông tin đăng nhập, mật khẩu đã băm và các hóa đơn, sổ thu chi, tài liệu, hồ sơ bạn cung cấp để vận hành chức năng bạn sử dụng. Đọc chữ từ tệp và tra cứu tài khoản chạy trên máy chủ ứng dụng. Không có quảng cáo hay công cụ theo dõi hành vi của bên thứ ba."],
      ["access", "Bảo vệ thông tin tài khoản", "Dữ liệu của tài khoản riêng được giới hạn theo phiên đăng nhập và quyền truy cập, không công khai cho tài khoản khác. Tài khoản mẫu dùng chung chỉ dành cho dữ liệu giả lập. Tài liệu trong kho kiến thức chỉ được chia sẻ sau khi quản trị viên xác nhận xuất bản. Bản trực tuyến được lưu tại Render; bản chạy trên máy cá nhân sử dụng máy chủ đã cấu hình. Người quản trị hạ tầng có khả năng truy cập dữ liệu để vận hành hệ thống."],
      ["assistant", "Sử dụng Trợ lý du học", t.purpose + " " + t.processing + " " + t.demo + " " + t.scope + " " + t.excluded + " " + t.adult],
      ["retention", "Lưu trữ và thu hồi sự đồng ý", "Hội thoại chỉ được giữ trong bộ nhớ tab, không được lưu vào cơ sở dữ liệu hoặc nhật ký ứng dụng. Sự đồng ý có hiệu lực trong phiên đăng nhập, tối đa một giờ. Nhật ký chỉ ghi nhận quyền, phiên bản điều khoản, thời gian và sự kiện gửi, không ghi nội dung chat. Bạn có thể thu hồi sự đồng ý trong Tài khoản. " + t.revokeNote],
      ["files", "Quyền kiểm soát tệp và dữ liệu", "Chỉ tệp bạn chọn được xử lý sau khi bạn đồng ý. Bạn có thể tải lại hoặc xóa tài liệu chưa được hợp đồng hay hồ sơ tham chiếu; tệp hồ sơ nháp có thể gỡ. Tài liệu đã được tham chiếu và hồ sơ khóa được giữ để đối chiếu. Chưa có chức năng tự xóa toàn bộ tài khoản hoặc xóa bản sao lưu theo yêu cầu; liên hệ team quản trị để được hỗ trợ."],
      ["device", "Cookie và quyền thiết bị", "Cookie đăng nhập HttpOnly duy trì phiên; trình duyệt lưu tùy chọn ngôn ngữ, sáng/tối và hướng dẫn. Demo không xin quyền camera, micro, vị trí, danh bạ hoặc đọc toàn bộ ổ đĩa. Yêu cầu tỷ giá tham chiếu không gửi thông tin tài khoản tới nguồn tỷ giá. Chưa có kết nối ngân hàng hoặc công ty bảo hiểm."],
      ["contact", "Hỗ trợ và giới hạn", "Đây là sản phẩm dự thi, chưa có chứng nhận tuân thủ pháp luật hoặc kiểm toán bảo mật độc lập. Bộ lọc thông tin nhạy cảm không bảo đảm ẩn danh hoàn toàn. Dịch vụ AI bên ngoài có điều khoản xử lý riêng, vì vậy không cung cấp thông tin cá nhân, sức khỏe, mật khẩu hay bí mật trong chat. Liên hệ team qua kho mã nguồn để báo lỗi hoặc yêu cầu hỗ trợ; không đưa dữ liệu cá nhân vào bài báo lỗi công khai."],
    ],
    en: [
      ["data", "Information used", "Demo stores login details, password hashes, and the invoices, finance records, documents and claim-preparation records you provide to operate the features you use. File reading and account lookup run on the application server. There are no ads or third-party behavioural tracking tools."],
      ["access", "Account information protection", "Private-account data is restricted by login sessions and access permissions, not published to other accounts. The shared sample account is for fictional data only. Knowledge-base documents are shared only after administrator publication consent. Render hosts the online app; local installations use their configured server. Infrastructure administrators can access data to operate the system."],
      ["assistant", "Using the study-abroad assistant", t.purpose + " " + t.processing + " " + t.demo + " " + t.scope + " " + t.excluded + " " + t.adult],
      ["retention", "Retention and consent withdrawal", "Conversation exists only in tab memory, not in the application database or logs. Consent lasts for the login session, up to one hour. Audit records contain permission, terms version, time and dispatch events, not chat content. Withdraw consent in Account settings. " + t.revokeNote],
      ["files", "File and data controls", "Only selected files are processed after you agree. Download or delete documents not referenced by policies or claims, and remove draft attachments. Referenced documents and locked claims are retained for review. Full account erasure and requested backup deletion are not yet self-service features; contact the team for help."],
      ["device", "Cookies and device permissions", "A necessary HttpOnly cookie maintains login; the browser stores language, theme and guide preferences. Demo requests no camera, microphone, location, contacts or full-disk access. Generic reference-rate queries do not share account information. No bank or insurer connection is configured."],
      ["contact", "Support and limits", "This competition product has no independent security audit or legal compliance certification. Sensitive-information filters cannot guarantee anonymity. External AI processing has separate service terms, so do not enter personal, health, password or confidential information in chat. Contact the team through the source repository; keep personal data out of public issue reports."],
    ],
    zh: [
      ["data", "使用的信息", "Demo 保存登录信息、密码哈希及您提供的账单、财务记录、文档和理赔准备记录，以运行您使用的功能。文件读取和账户查询在应用服务器运行，无广告或第三方行为跟踪工具。"],
      ["access", "账户信息保护", "私人账户数据受登录会话和访问权限限制，不向其他账户公开。共享示例账户仅用于虚构数据。知识库文档仅在管理员同意发布后共享。线上应用由 Render 托管，本地应用使用配置的服务器；基础设施管理员可为系统运行访问数据。"],
      ["assistant", "使用留学助手", t.purpose + " " + t.processing + " " + t.demo + " " + t.scope + " " + t.excluded + " " + t.adult],
      ["retention", "保留与撤回同意", "对话仅保留在标签页内存，不保存到应用数据库或日志。同意仅在登录会话中有效，最长一小时。日志只记录权限、条款版本、时间及发送事件，不记录对话内容。可在账户设置撤回同意。" + t.revokeNote],
      ["files", "文件与数据控制", "仅在同意后处理所选文件。可下载或删除未被保单或理赔引用的文档，并移除草稿附件；已引用文档及锁定理赔记录会保留以供核对。目前不支持自助删除整个账户或按需删除备份，请联系团队获取帮助。"],
      ["device", "Cookie 与设备权限", "必要的 HttpOnly Cookie 维持登录，浏览器保存语言、主题和指南偏好。不申请摄像头、麦克风、位置、通讯录或整个磁盘权限。通用参考汇率查询不发送账户信息，未连接银行或保险公司。"],
      ["contact", "支持与限制", "此参赛产品尚无独立安全审计或法律合规认证。敏感信息过滤无法保证完全匿名。外部 AI 服务有独立处理条款，请勿在聊天中输入个人、健康、密码或机密信息。请通过源码仓库联系团队，不要在公开问题报告中提供个人数据。"],
    ],
  }[locale];
  return <main className="privacy-page"><Link className="text-link" href="/account">← Demo</Link><h1>{t.policy}</h1><p className="small muted">19/10/2026</p>
    {sections.map(([id, title, body]) => <section id={id} key={id}>{id === "assistant" && <span id="gemini" aria-hidden="true"/>}<h2>{title}</h2><p>{body}</p></section>)}
    {(["documents", "invoice-ocr", "claim-attachments", "rag-corpus", "rag-publish"] as const).map(purpose => {
      const notice = fileNotice(locale, purpose);
      return <section id={purpose} key={purpose}><h2>{notice.title}</h2><p>{notice.summary} {notice.limit}</p><p>{t.upload}</p></section>;
    })}
    <p><a className="text-link" href="https://ai.google.dev/gemini-api/terms" target="_blank" rel="noreferrer">{t.terms} ↗</a> · <a className="text-link" href="https://github.com/hung230206/AI4S" target="_blank" rel="noreferrer">GitHub</a></p>
  </main>;
}
