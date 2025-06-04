
import { cn } from '@/lib/utils';

interface FooterProps {
  className?: string;
}

export function Footer({ className }: FooterProps) {
  const currentYear = new Date().getFullYear();
  return (
    <footer className={cn("bg-background/50 border-t py-4 mt-auto", className)}> {/* Subtle background, less padding */}
      <div className="container mx-auto px-4 text-center text-xs text-muted-foreground"> {/* Smaller text */}
        <p>&copy; {currentYear} Employability Prediction. Crafted by Pinaki, Anuvab, Debanjan & Soumyajit.</p>
        {/* Example links */}
        {/* <div className="mt-3 space-x-4">
          <a href="#" className="hover:text-foreground transition-colors">Privacy Policy</a>
          <span className="text-border">|</span>
          <a href="#" className="hover:text-foreground transition-colors">Terms of Service</a>
        </div> */}
      </div>
    </footer>
  );
}
