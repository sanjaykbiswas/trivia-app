
import React from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface PirateButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent';
  children: React.ReactNode;
  icon?: React.ReactNode;
}

const PirateButton: React.FC<PirateButtonProps> = ({
  variant = 'primary',
  children,
  icon,
  className,
  ...props
}) => {
  return (
    <Button
      className={cn(
        'rounded-full font-semibold py-6 flex items-center justify-center gap-2 text-base',
        variant === 'primary' 
          ? 'bg-pirate-navy text-white border-2 border-pirate-gold hover:bg-pirate-navy/90'
          : variant === 'secondary'
            ? 'bg-white text-pirate-navy border-2 border-pirate-navy hover:bg-gray-100'
            : 'bg-pirate-accent text-white border-2 border-pirate-gold hover:bg-pirate-accent/90',
        className
      )}
      {...props}
    >
      {children}
      {icon && <span className="ml-2">{icon}</span>}
    </Button>
  );
};

export default PirateButton;
