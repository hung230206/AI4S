import type {Metadata} from "next";
import {Shell} from "@/components/shell";
import "./globals.css";
export const metadata: Metadata = {title: "Demo | Khoản phí du học & tài liệu bảo hiểm", description: "Quản lý hóa đơn CNY, tính giá trị tham chiếu bằng VND và tra cứu điều khoản từ tài liệu của bạn. Thanh toán ở chế độ thử nghiệm."};
export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {return <html lang="vi" data-scroll-behavior="smooth"><body><Shell>{children}</Shell></body></html>;}
