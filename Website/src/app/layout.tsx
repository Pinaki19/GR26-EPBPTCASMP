
import type { Metadata } from 'next';
import { Lato, Montserrat } from 'next/font/google'; // Import Lato and Montserrat
import { Toaster } from "@/components/ui/toaster";
import './globals.css';
import { cn } from '@/lib/utils';

// Initialize Lato font for body text
const lato = Lato({
  subsets: ['latin'],
  weight: ['400', '700'], // Include weights needed for body text
  variable: '--font-sans', // Define CSS variable for sans-serif font
});

// Initialize Montserrat font for headings
const montserrat = Montserrat({
  subsets: ['latin'],
  weight: ['600', '700', '800'], // Include weights needed for headings
  variable: '--font-heading', // Define CSS variable for heading font
});

export const metadata: Metadata = {
  title: 'Employability Prediction', // Updated title
  description: 'Leveraging AI to analyze social media for employability insights.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    // Add suppressHydrationWarning to html tag to handle potential extension mismatches
    // Add both font variable classes to html tag
    <html lang="en" className={cn("h-full", lato.variable, montserrat.variable)} suppressHydrationWarning>
      {/*
        Apply h-full to body. Use font-sans utility which maps to --font-sans variable.
        Headings will use --font-heading via Tailwind config.
      */}
      {/* Add suppressHydrationWarning to body tag as well to specifically ignore extension attributes */}
      <body className={cn("h-full font-sans antialiased")} suppressHydrationWarning>
        {children}
        <Toaster /> {/* Toaster for notifications */}
      </body>
    </html>
  );
}
