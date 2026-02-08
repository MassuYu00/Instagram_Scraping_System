export const metadata = {
    title: 'Toronto Info Scraper',
    description: 'Admin panel for Toronto Info scraper',
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
