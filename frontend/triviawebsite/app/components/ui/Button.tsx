import React from 'react';
import { twMerge } from 'tailwind-merge';
import Typography from './Typography';

type ButtonVariant = 'contained' | 'outlined' | 'text';
type ButtonSize = 'small' | 'medium' | 'large';

interface ButtonProps {
  onClick: () => void;
  title: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  className?: string;
  testId?: string;
}

/**
 * Button component
 * Reusable button with different variants and states
 */
const Button: React.FC<ButtonProps> = ({
  onClick,
  title,
  variant = 'contained',
  size = 'medium',
  disabled = false,
  loading = false,
  fullWidth = false,
  className = '',
  testId,
}) => {
  // Base styles for all buttons
  const baseStyles = 'rounded-2xl justify-center items-center flex-row transition';

  // Get size-specific classes
  const getSizeClasses = () => {
    switch (size) {
      case 'small':
        return 'py-2 px-4';
      case 'large':
        return 'py-4 px-6';
      default: // medium
        return 'py-3 px-5';
    }
  };

  // Get variant-specific classes
  const getVariantClasses = () => {
    switch (variant) {
      case 'outlined':
        return `bg-transparent border border-solid ${
          disabled ? 'border-text-disabled text-text-disabled' : 'border-primary-main text-primary-main'
        }`;
      case 'text':
        return `bg-transparent px-2 ${
          disabled ? 'text-text-disabled' : 'text-primary-main'
        }`;
      default: // contained
        return `${
          disabled ? 'bg-gray-400' : 'bg-primary-main'
        } text-primary-contrastText`;
    }
  };

  // Get text style
  const getTextVariant = (): 'buttonSmall' | 'buttonMedium' | 'buttonLarge' => {
    switch (size) {
      case 'small':
        return 'buttonSmall';
      case 'large':
        return 'buttonLarge';
      default: // medium
        return 'buttonMedium';
    }
  };

  // Get text color
  const getTextColor = () => {
    if (variant === 'contained') {
      return 'text-primary-contrastText';
    }
    return disabled ? 'text-text-disabled' : 'text-primary-main';
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={twMerge(
        baseStyles,
        getSizeClasses(),
        getVariantClasses(),
        fullWidth ? 'w-full' : 'w-auto',
        className
      )}
      data-testid={testId}
    >
      {loading ? (
        <div className="w-5 h-5 border-2 border-t-transparent border-white rounded-full animate-spin"></div>
      ) : (
        <Typography
          variant={getTextVariant()}
          color={getTextColor()}
        >
          {title}
        </Typography>
      )}
    </button>
  );
};

export default Button;