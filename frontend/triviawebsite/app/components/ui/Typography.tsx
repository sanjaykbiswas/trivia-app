import React from 'react';
import { twMerge } from 'tailwind-merge';

// Available typography variants matching the mobile app
type TypographyVariant =
  | 'heading1'
  | 'heading2'
  | 'heading3'
  | 'heading4'
  | 'heading5'
  | 'bodyLarge'
  | 'bodyMedium'
  | 'bodySmall'
  | 'buttonLarge'
  | 'buttonMedium'
  | 'buttonSmall'
  | 'caption'
  | 'overline';

interface TypographyProps {
  children: React.ReactNode;
  variant?: TypographyVariant;
  className?: string;
  color?: string;
  align?: 'left' | 'right' | 'center' | 'justify';
}

// Typography styling maps based on the mobile app's typography
const variantClasses: Record<TypographyVariant, string> = {
  heading1: 'text-4xl font-bold leading-10 tracking-wide',
  heading2: 'text-3xl font-bold leading-9 tracking-wide',
  heading3: 'text-2xl font-semibold leading-8 tracking-normal',
  heading4: 'text-xl font-semibold leading-7 tracking-normal',
  heading5: 'text-lg font-medium leading-6 tracking-normal',
  bodyLarge: 'text-lg font-normal leading-7 tracking-wide',
  bodyMedium: 'text-base font-normal leading-6 tracking-wide',
  bodySmall: 'text-sm font-normal leading-5 tracking-wide',
  buttonLarge: 'text-base font-bold leading-6 tracking-wide',
  buttonMedium: 'text-base font-medium leading-6 tracking-wide',
  buttonSmall: 'text-sm font-medium leading-5 tracking-wide',
  caption: 'text-xs font-normal leading-4 tracking-wider',
  overline: 'text-xs font-medium leading-4 tracking-widest uppercase',
};

const alignClasses: Record<NonNullable<TypographyProps['align']>, string> = {
  left: 'text-left',
  right: 'text-right',
  center: 'text-center',
  justify: 'text-justify',
};

const Typography = ({
  children,
  variant = 'bodyMedium',
  className = '',
  color = 'text-text-primary',
  align = 'left',
}: TypographyProps) => {
  // Choose HTML element based on variant
  const getElement = () => {
    if (variant.startsWith('heading')) {
      const level = parseInt(variant.charAt(variant.length - 1));
      switch (level) {
        case 1:
          return 'h1';
        case 2:
          return 'h2';
        case 3:
          return 'h3';
        case 4:
          return 'h4';
        case 5:
          return 'h5';
        default:
          return 'h6';
      }
    }
    return 'p';
  };

  const Element = getElement();
  
  return React.createElement(
    Element,
    {
      className: twMerge(
        variantClasses[variant],
        alignClasses[align],
        color.startsWith('text-') ? color : `text-${color}`,
        className
      )
    },
    children
  );
};

export default Typography;