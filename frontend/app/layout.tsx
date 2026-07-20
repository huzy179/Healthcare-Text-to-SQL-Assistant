import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Healthcare Text-to-SQL",
  description: "Role-aware healthcare Text-to-SQL demo over PostgreSQL",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
