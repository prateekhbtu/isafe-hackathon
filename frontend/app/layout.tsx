import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'MDRS - Multimodal Deception Risk Scorer',
  description: 'AI-Assisted Triage for Media Authenticity',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
