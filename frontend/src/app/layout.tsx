import type {Metadata} from "next";
import {Providers} from "@/components/providers";
import {Shell} from "@/components/shell";
import "./globals.css";
export const metadata: Metadata = {
  title: "Demo | Khoản phí du học & tài liệu bảo hiểm",
  description: "Quản lý hóa đơn CNY, tính giá trị tham chiếu bằng VND và tra cứu điều khoản từ tài liệu của bạn. Thanh toán ở chế độ thử nghiệm.",
};
export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return (
    <html lang="vi" data-scroll-behavior="smooth" suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{__html: `(function(){try{var t=localStorage.getItem('baoan.theme');var d=t==='dark'||(t!=='light'&&matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.classList.toggle('dark',d);document.documentElement.style.colorScheme=d?'dark':'light'}catch(e){}})()`}}/></head>
      <body>
        <Providers>
          <Shell>{children}</Shell>
        </Providers>
      </body>
    </html>
  );
}
