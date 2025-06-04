'use client';

import React, { useState, useRef, useEffect } from 'react';
import type React_Type from 'react';
import { Footer } from '@/components/layout/footer';
import { AssessmentCard } from '@/components/assessment-card';
import { User, Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from "@/hooks/use-toast";

interface CardData {
  id: 'self' | 'candidate';
  title: string;
  description: string;
  icon: React.ReactNode;
  buttonText: string;
}

export default function Home() {
  const [centeredCard, setCenteredCard] = useState<'self' | 'candidate' | null>(null);
  const [closingCardId, setClosingCardId] = useState<'self' | 'candidate' | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [initialLoad, setInitialLoad] = useState(true);
  const { toast } = useToast();

  const selfAssessmentData: CardData = {
    id: 'self',
    icon: <User />,
    title: "Self-Assessment Analysis",
    description: "Analyze your own social media profile or text data to understand your personality traits and cognitive indicators relevant to employability.",
    buttonText: "Start Self-Analysis",
  };

  const candidateAssessmentData: CardData = {
    id: 'candidate',
    icon: <Users />,
    title: "Candidate Assessment",
    description: "Assess a potential candidate's employability by analyzing their social media profile or provided text for personality and cognitive insights.",
    buttonText: "Assess Candidate",
  };

  const cardsData = [selfAssessmentData, candidateAssessmentData];

  const handleCardClick = (id: 'self' | 'candidate') => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setClosingCardId(null); // Ensure closing state is reset if a new card is clicked quickly
    setInitialLoad(false); // Explicitly set initialLoad to false on interaction
    setCenteredCard(id);
  };

  const handleCloseCentered = (e?: React.MouseEvent) => {
    if (e) {
      e.stopPropagation(); // Prevent clicks on the overlay from propagating
    }
    if (centeredCard) {
      setClosingCardId(centeredCard); // Start closing animation state
      setCenteredCard(null); // Remove centered state

      // Clear previous timeout if exists
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set a timer to remove the closing state after the animation duration
      timeoutRef.current = setTimeout(() => {
        setClosingCardId(null); // Reset closing state after animation completes
        timeoutRef.current = null;
      }, 500); // Match duration of the closing animation (duration-500)
    }
  };

  /*
   const handleUrlSubmit = (cardId: 'self' | 'candidate', url: string) => {
    console.log(`Submitting URL for ${cardId}:`, url);
    toast({
      title: "URL Submitted",
      description: `Analysis started for ${cardId}. Please wait...`,
      variant: "default",
    });
    // Consider closing card or showing loading state inside
    // handleCloseCentered(); // Optionally close after submit
  };
  */
  const handleUrlSubmit = (cardId: 'self' | 'candidate', url: string) => {
  const socket = new WebSocket("ws://localhost:8090/ws"); // Must match port used in api.py

  socket.onopen = () => {
    socket.send(JSON.stringify({
      type: "Profile",
      data: url,
    }));
    console.log("Profile URL sent to backend:", url);
  };

  socket.onerror = (err) => {
    console.error("WebSocket error:", err);
  };

  socket.onmessage = (event) => {
    console.log("Backend message:", event.data);
  };

  toast({
    title: "URL Submitted",
    description: `Started analysis for ${cardId}.`,
  });
};


  // Effect to handle initial load animation state only once
 useEffect(() => {
    const timer = setTimeout(() => {
      // Only set initialLoad to false if it's currently true and no card is centered
      if (initialLoad && !centeredCard) {
        setInitialLoad(false);
      }
    }, 50); // Small delay to ensure initial render completes
    return () => clearTimeout(timer);
    // Depend on initialLoad and centeredCard to correctly manage the state transition
  }, [initialLoad, centeredCard]);


  // Effect to clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const isCardCentered = !!centeredCard; // True if a card is actively centered
  const isCardClosing = !!closingCardId; // True if a card is in the process of closing
  const isBackgroundFaded = isCardCentered; // Background elements fade when a card is centered
  // isAnimating should be true if a card is centering, centered, or closing
  const isAnimating = isCardCentered || isCardClosing;

  return (
    // Main container: Full height, flex column, animated gradient background, no overflow
    <div className={cn(
      "flex flex-col h-screen overflow-hidden", // Ensure no overflow
      "bg-gradient-to-br from-background via-secondary/30 to-accent/20", // Adjusted gradient intensity
      "bg-[length:300%_300%]", // Set background size for animation
      "animate-gradient" // Apply the gradient animation
    )}>
      {/* Overlay: Appears when a card is centered */}
      {isCardCentered && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-md z-40 animate-in fade-in-0 duration-500" // Increased blur and darkness
          onClick={handleCloseCentered} // Close card when overlay is clicked
        />
      )}

      {/* Main Content Area: Grows to fill space, centered items, relative positioning, NO SCROLLING */}
      {/* Adjusted padding for better vertical centering */}
      <main className="flex-grow flex flex-col items-center justify-center container mx-auto px-4 py-6 md:py-8 relative overflow-hidden">
        {/* Title Section: Centered text, transitions with content fade */}
        <section className={cn(
            "text-center mb-6 md:mb-8 transition-all duration-500 ease-in-out", // Increased bottom margin slightly
             // Fade/scale out when card is centered, fade/scale in otherwise
            isBackgroundFaded ? "opacity-0 scale-90 pointer-events-none" : "opacity-100 scale-100", // Slightly stronger scale down
            initialLoad && "opacity-0", // Initially hidden for animation
             // Slide in after initial load if not faded
            !initialLoad && !isBackgroundFaded && "animate-in fade-in slide-in-from-bottom-8 duration-500 delay-200 fill-mode-backwards" // Slightly shorter slide
           )}>
          {/* Gradient Animated Title - Apply heading font, increased size, adjusted leading and padding */}
          <h1 className="text-5xl sm:text-6xl font-extrabold mb-2 font-heading bg-gradient-to-r from-primary via-accent to-primary bg-[length:300%_300%] bg-clip-text text-transparent animate-gradient leading-tight pb-2"> {/* Adjusted mb, leading and added pb */}
            Employability Prediction
          </h1>
          {/* Description Text - Use standard sans font */}
          <p className="text-base sm:text-lg text-foreground/70 max-w-3xl mx-auto leading-relaxed"> {/* Slightly reduced opacity */}
            Analyze personality & cognitive traits from social media for employability prediction.
          </p>
        </section>

        {/* Cards Grid: Displays assessment cards */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8 max-w-5xl mx-auto w-full relative"> {/* Reduced max-width slightly */}
           {cardsData.map((card, index) => (
             // Wrapper div for handling positioning and animation of each card
             <div
                key={card.id}
                className={cn(
                  "transition-all duration-500 ease-in-out transform-gpu will-change-transform,opacity,scale", // Base transition styles
                   // State: Card is centered
                  centeredCard === card.id && "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[90%] max-w-lg scale-100 z-50 opacity-100",
                   // State: Another card is centered (this one fades out)
                  centeredCard && centeredCard !== card.id && "opacity-0 scale-90 pointer-events-none",
                   // State: This card is closing
                  closingCardId === card.id && "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[90%] max-w-lg z-30 opacity-0 scale-95",
                   // State: Initial Load (hidden before animation)
                   initialLoad && "opacity-0 translate-y-10 scale-95",
                   // State: Idle (visible in grid after initial load, not animating) - Apply entry animation
                  !initialLoad && !isAnimating && !centeredCard && (index === 0 ? "animate-in fade-in slide-in-from-bottom-10 duration-500 delay-300 fill-mode-backwards" : "animate-in fade-in slide-in-from-bottom-10 duration-500 delay-400 fill-mode-backwards"), // Adjusted slide distance
                   // State: Idle (visible in grid) - Ensure final styles are applied if animations finished
                  !initialLoad && !isAnimating && !centeredCard && "opacity-100 scale-100 translate-y-0"
                )}
              >
                {/* Render the AssessmentCard component */}
                <AssessmentCard
                  {...card}
                  icon={React.cloneElement(card.icon as React.ReactElement, { className: "w-10 h-10 md:w-11 md:h-11 text-primary" })} // Slightly smaller icon
                   onClick={() => !isAnimating && handleCardClick(card.id)} // Prevent click during animation
                  isCentered={centeredCard === card.id}
                  onClose={handleCloseCentered}
                  onSubmitUrl={(url) => handleUrlSubmit(card.id, url)}
                />
              </div>
           ))}
        </section>
      </main>

      {/* Footer: Fades with content, handles initial load animation */}
     <Footer className={cn(
          "transition-opacity duration-500 shrink-0",
          // Fade out when card is centered, fade in otherwise
          isBackgroundFaded ? "opacity-0 pointer-events-none" : "opacity-100",
          initialLoad && "opacity-0", // Initially hidden for animation
          // Slide in after initial load if not faded
          !initialLoad && !isBackgroundFaded && "animate-in fade-in slide-in-from-bottom-8 duration-500 delay-300 fill-mode-backwards" // Adjusted slide distance
        )}
      />
    </div>
  );
}
