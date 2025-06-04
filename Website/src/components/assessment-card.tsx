
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowRight, X, Link as LinkIcon, Send } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AssessmentCardProps {
  id: 'self' | 'candidate';
  icon: React.ReactNode;
  title: string;
  description: string;
  buttonText: string;
  onClick: () => void;
  isCentered?: boolean;
  onClose?: (e?: React.MouseEvent) => void;
  onSubmitUrl: (url: string) => void;
}

export function AssessmentCard({
  id,
  icon,
  title,
  description,
  buttonText,
  onClick,
  isCentered = false,
  onClose,
  onSubmitUrl,
}: AssessmentCardProps) {
  const [url, setUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Reset state when the card is no longer centered
    if (!isCentered) {
      setUrl('');
      setIsSubmitting(false);
    }
  }, [isCentered]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return; // Prevent submission if URL is empty
    setIsSubmitting(true);
    onSubmitUrl(url);
    // isSubmitting state will be managed by the parent or reset on card close
  };

  return (
    <Card className={cn(
      "flex flex-col bg-card shadow-lg transition-all duration-500 ease-in-out relative overflow-hidden rounded-xl border border-border/50", // Base card styles
      !isCentered && "hover:shadow-xl hover:border-primary/60 hover:scale-[1.02] cursor-pointer transition-shadow,transform", // Hover effects for non-centered card with shadow transition
      isCentered && "w-[95%] max-w-lg" // Styles when centered
    )}
      onClick={!isCentered ? onClick : undefined} // Only clickable when not centered
      tabIndex={-1} // Prevent blinking cursor on the card itself
    >
      {/* Close button, only visible when centered */}
      {isCentered && onClose && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-3 right-3 text-muted-foreground hover:text-foreground z-20 rounded-full bg-card/50 hover:bg-card/80" // Positioned top-right, subtle background
          onClick={onClose}
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </Button>
      )}

      {/* Card Header: Icon and Title */}
      <CardHeader className={cn(
            "items-center text-center p-4 pb-2 pt-6 relative z-10", // Adjusted padding, centered items
          )}>
         {/* Icon Wrapper: Styled background, shadow, border */}
         <div className={cn(
             "mb-3 text-primary bg-card p-3 rounded-full shadow-md border border-border/50", // Card background, rounded, shadow, border
             isCentered && "mb-4" // Slightly more margin when centered
         )}>
             {/* Clone icon to apply common styles if needed */}
             {React.cloneElement(icon as React.ReactElement)}
         </div>

         {/* Card Title - Apply heading font, reduced boldness */}
         <CardTitle className={cn(
             "text-xl md:text-2xl font-medium pt-0 font-heading" // Use heading font, changed font-semibold to font-medium
         )}>{title}</CardTitle>
      </CardHeader>

      {/* Card Content: Description */}
      <CardContent className="flex-grow text-center px-4 pb-4 pt-0">
        <CardDescription className="text-sm md:text-base text-muted-foreground leading-relaxed">{description}</CardDescription>
      </CardContent>

      {/* Card Footer: Button or Form */}
      <CardFooter className={cn(
          "justify-center p-4 pt-0 flex-col space-y-3",
          !isCentered && "bg-secondary/30", // Subtle background when not centered
          isCentered && "bg-transparent", // Transparent background when centered
          "rounded-b-xl border-t border-border/50" // Bottom rounded corners and top border
      )}>
        {!isCentered ? (
          // Initial Button (when not centered)
          <Button
             variant="default" // Use the primary button style
             size="default"
             className={cn(
               "mt-2 w-full max-w-xs transition-transform duration-200 hover:scale-105 group font-semibold", // Added hover scale effect, font-semibold
                // Animated gradient background with slower speed
               "bg-gradient-to-r from-primary via-accent to-primary bg-[length:300%_300%] animate-gradient"
             )}
             onClick={onClick}
             style={{ animationDuration: '15s' }} // Explicitly set slower animation duration
           >
             {buttonText}
             {/* Arrow icon animates on hover */}
             <ArrowRight className="ml-2 h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
          </Button>
        ) : (
          // Form (when centered)
          <form onSubmit={handleSubmit} className="w-full flex flex-col items-center space-y-3 animate-in fade-in duration-300 delay-150 px-2"> {/* Fade-in animation for form */}
            {/* URL Input Field */}
            <div className="relative w-full max-w-md">
              <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" /> {/* Icon inside input */}
              <Input
                type="url"
                placeholder="Paste social media profile URL..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                required
                className="pl-9 pr-4 py-2 text-sm border-input bg-background text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/80 focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:border-primary/50 transition-all duration-300 shadow-sm hover:shadow-md focus:shadow-lg focus:border-primary" // Enhanced focus styles with transitions
                aria-label="Social media profile URL"
                disabled={isSubmitting} // Disable input while submitting
              />
            </div>
            {/* Submit Button */}
            <Button
              type="submit"
              variant="default" // Primary button style
              size="default"
              className={cn(
                "w-full max-w-md transition-transform duration-200 hover:scale-105 font-semibold", // Added hover scale effect, font-semibold
                 // Apply gradient animation with slow speed
                "bg-gradient-to-r from-primary via-accent to-primary bg-[length:300%_300%] animate-gradient"
              )}
               style={{ animationDuration: '15s' }} // Explicitly set slower animation duration
              disabled={isSubmitting || !url.trim()} // Disable if submitting or URL is empty
            >
              {isSubmitting ? 'Analyzing...' : 'Submit URL'}
              {!isSubmitting && <Send className="ml-2 h-4 w-4" />} {/* Show Send icon when not submitting */}
            </Button>
          </form>
        )}
      </CardFooter>
    </Card>
  );
}
