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
    title: "Batch Assessment",
    description: "Assess a potential candidate's employability by analyzing their social media profile or provided text for personality and cognitive insights.",
    buttonText: "Assess Candidate",
  };

  const cardsData = [selfAssessmentData, candidateAssessmentData];

  const handleCardClick = (id: 'self' | 'candidate') => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setClosingCardId(null); 
    setInitialLoad(false); 
    setCenteredCard(id);
  };

  const handleCloseCentered = (e?: React.MouseEvent) => {
    if (e) {
      e.stopPropagation(); 
    }
    if (centeredCard) {
      setClosingCardId(centeredCard); 
      setCenteredCard(null); 

      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        setClosingCardId(null); 
        timeoutRef.current = null;
      }, 500); 
    }
  };

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


 useEffect(() => {
    const timer = setTimeout(() => {
      if (initialLoad && !centeredCard) {
        setInitialLoad(false);
      }
    }, 50); 
    return () => clearTimeout(timer);
  }, [initialLoad, centeredCard]);


  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const isCardCentered = !!centeredCard; 
  const isCardClosing = !!closingCardId; 
  const isBackgroundFaded = isCardCentered; 
  const isAnimating = isCardCentered || isCardClosing;

  return (
    <div className={cn(
      "flex flex-col h-screen overflow-hidden", 
      "bg-gradient-to-br from-background via-secondary/30 to-accent/20", 
      "bg-[length:300%_300%]", 
      "animate-gradient" 
    )}>
      {isCardCentered && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-md z-40 animate-in fade-in-0 duration-500" 
          onClick={handleCloseCentered} 
        />
      )}

      <main className="flex-grow flex flex-col items-center justify-center container mx-auto px-4 py-6 md:py-8 relative overflow-hidden">
        <section className={cn(
            "text-center mb-6 md:mb-8 transition-all duration-500 ease-in-out", 
            isBackgroundFaded ? "opacity-0 scale-90 pointer-events-none" : "opacity-100 scale-100", 
            initialLoad && "opacity-0", 
            !initialLoad && !isBackgroundFaded && "animate-in fade-in slide-in-from-bottom-8 duration-500 delay-200 fill-mode-backwards" 
           )}>
          <h1 className="text-5xl sm:text-6xl font-extrabold mb-4 font-heading bg-gradient-to-r from-primary via-accent to-primary bg-[length:300%_300%] bg-clip-text text-transparent animate-gradient leading-tight pb-2 pt-1">
            Employability Prediction Tool
          </h1>
          <p className="text-base sm:text-lg text-foreground/70 max-w-3xl mx-auto leading-relaxed">
            Analyze personality & cognitive traits from social media for employability prediction.
          </p>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8 max-w-5xl mx-auto w-full relative">
           {cardsData.map((card, index) => (
             <div
                key={card.id}
                className={cn(
                  "transition-all duration-500 ease-in-out transform-gpu will-change-transform,opacity,scale", 
                  centeredCard === card.id && "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 opacity-100",
                  centeredCard && centeredCard !== card.id && "opacity-0 scale-90 pointer-events-none",
                  closingCardId === card.id && "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-30 opacity-0 scale-95",
                   initialLoad && "opacity-0 translate-y-10 scale-95",
                  !initialLoad && !isAnimating && !centeredCard && (index === 0 ? "animate-in fade-in slide-in-from-bottom-10 duration-500 delay-300 fill-mode-backwards" : "animate-in fade-in slide-in-from-bottom-10 duration-500 delay-400 fill-mode-backwards"), 
                  !initialLoad && !isAnimating && !centeredCard && "opacity-100 scale-100 translate-y-0"
                )}
              >
                <AssessmentCard
                  {...card}
                  icon={React.cloneElement(card.icon as React.ReactElement, { className: "w-10 h-10 md:w-11 md:h-11 text-primary" })} 
                   onClick={() => !isAnimating && handleCardClick(card.id)} 
                  isCentered={centeredCard === card.id}
                  onClose={handleCloseCentered}
                  onSubmitUrl={(urls) => handleUrlSubmit(card.id, urls)}
                />
              </div>
           ))}
        </section>
      </main>

     <Footer className={cn(
          "transition-opacity duration-500 shrink-0",
          isBackgroundFaded ? "opacity-0 pointer-events-none" : "opacity-100",
          initialLoad && "opacity-0",
          !initialLoad && !isBackgroundFaded && "animate-in fade-in slide-in-from-bottom-8 duration-500 delay-300 fill-mode-backwards"
        )}
      />
    </div>
  );
}
