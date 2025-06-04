import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowRight, X, Link as LinkIcon, Send, PlusCircle } from 'lucide-react';
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
  onSubmitUrl: (urls: string[]) => void;
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
  const [inputUrls, setInputUrls] = useState<string[]>(['']);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Reset state when the card is no longer centered or when the id changes
    if (!isCentered) {
      setInputUrls(['']);
      setIsSubmitting(false);
    } else {
      // Ensure it resets to a single input if switching to 'self' or starting fresh
      setInputUrls(['']);
    }
  }, [isCentered, id]);

  const handleUrlChange = (index: number, value: string) => {
    const newUrls = [...inputUrls];
    newUrls[index] = value;
    setInputUrls(newUrls);
  };

  const handleAddUrlField = () => {
    if (id === 'candidate') {
      setInputUrls([...inputUrls, '']);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedUrls = inputUrls.map(u => u.trim()).filter(u => u !== '');
    if (trimmedUrls.length === 0) return; 
    setIsSubmitting(true);
    onSubmitUrl(trimmedUrls);
    // isSubmitting state will be managed by the parent or reset on card close/re-center
  };

  return (
    <Card className={cn(
      "flex flex-col bg-card shadow-lg transition-all duration-500 ease-in-out relative overflow-hidden rounded-xl border border-border/50",
      !isCentered && "hover:shadow-xl hover:border-primary/60 hover:scale-[1.02] cursor-pointer transition-shadow,transform",
      isCentered && (id === 'candidate' ? "w-[95%] max-w-xl" : "w-[95%] max-w-lg") // Stretch candidate card
    )}
      onClick={!isCentered ? onClick : undefined}
      tabIndex={-1}
    >
      {isCentered && onClose && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-3 right-3 text-muted-foreground hover:text-foreground z-20 rounded-full bg-card/50 hover:bg-card/80"
          onClick={onClose}
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </Button>
      )}

      <CardHeader className={cn(
            "items-center text-center p-4 pb-2 pt-6 relative z-10",
          )}>
         <div className={cn(
             "mb-3 text-primary bg-card p-3 rounded-full shadow-md border border-border/50",
             isCentered && "mb-4"
         )}>
             {React.cloneElement(icon as React.ReactElement)}
         </div>
         <CardTitle className={cn(
             "text-xl md:text-2xl font-medium pt-0 font-heading"
         )}>{title}</CardTitle>
      </CardHeader>

      <CardContent className="flex-grow text-center px-4 pb-4 pt-0">
        <CardDescription className="text-sm md:text-base text-muted-foreground leading-relaxed">{description}</CardDescription>
      </CardContent>

      <CardFooter className={cn(
          "justify-center p-4 pt-0 flex-col space-y-3",
          !isCentered && "bg-secondary/30",
          isCentered && "bg-transparent",
          "rounded-b-xl border-t border-border/50"
      )}>
        {!isCentered ? (
          <Button
             variant="default"
             size="default"
             className={cn(
               "mt-2 w-full max-w-xs transition-transform duration-200 hover:scale-105 group font-semibold",
               "bg-gradient-to-r from-primary via-accent to-primary bg-[length:300%_300%] animate-gradient"
             )}
             onClick={onClick}
             style={{ animationDuration: '15s' }}
           >
             {buttonText}
             <ArrowRight className="ml-2 h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
          </Button>
        ) : (
          <form onSubmit={handleSubmit} className="w-full flex flex-col items-center space-y-3 animate-in fade-in duration-300 delay-150 px-2">
            {id === 'self' && (
              <div className="relative w-full max-w-md">
                <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="url"
                  placeholder="Paste social media profile URL..."
                  value={inputUrls[0]}
                  onChange={(e) => handleUrlChange(0, e.target.value)}
                  required
                  className="pl-9 pr-4 py-2 text-sm border-input bg-background text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/80 focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:border-primary/50 transition-all duration-300 shadow-sm hover:shadow-md focus:shadow-lg focus:border-primary"
                  aria-label="Social media profile URL"
                  disabled={isSubmitting}
                />
              </div>
            )}
            {id === 'candidate' && inputUrls.map((url, index) => (
              <div key={index} className="relative w-full max-w-md">
                <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="url"
                  placeholder={`Paste social media profile URL ${index + 1}...`}
                  value={url}
                  onChange={(e) => handleUrlChange(index, e.target.value)}
                  required={index === 0 && inputUrls.length === 1} // Only require if it's the sole input field
                  className="pl-9 pr-4 py-2 text-sm border-input bg-background text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/80 focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:border-primary/50 transition-all duration-300 shadow-sm hover:shadow-md focus:shadow-lg focus:border-primary"
                  aria-label={`Social media profile URL ${index + 1}`}
                  disabled={isSubmitting}
                />
              </div>
            ))}
            {id === 'candidate' && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAddUrlField}
                className="w-full max-w-md flex items-center justify-center text-sm"
                disabled={isSubmitting}
              >
                <PlusCircle className="mr-2 h-4 w-4" />
                Add another URL
              </Button>
            )}
            <Button
              type="submit"
              variant="default"
              size="default"
              className={cn(
                "w-full max-w-md transition-transform duration-200 hover:scale-105 font-semibold",
                "bg-gradient-to-r from-primary via-accent to-primary bg-[length:300%_300%] animate-gradient"
              )}
               style={{ animationDuration: '15s' }}
              disabled={isSubmitting || inputUrls.every(url => !url.trim())}
            >
              {isSubmitting ? 'Analyzing...' : 'Submit URL(s)'}
              {!isSubmitting && <Send className="ml-2 h-4 w-4" />}
            </Button>
          </form>
        )}
      </CardFooter>
    </Card>
  );
}
