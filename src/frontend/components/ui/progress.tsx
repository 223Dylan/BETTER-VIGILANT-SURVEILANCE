import React from 'react';

interface ProgressProps {
  value: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  className = '',
  showLabel = false,
  size = 'md'
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const sizeClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4'
  };

  const baseClasses = 'w-full overflow-hidden rounded-full bg-secondary';
  const classes = `${baseClasses} ${sizeClasses[size]} ${className}`;

  return (
    <div className="w-full">
      <div className={classes}>
        <div
          className="h-full bg-primary transition-all duration-300 ease-in-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="mt-2 text-sm text-muted-foreground text-center">
          {Math.round(percentage)}%
        </div>
      )}
    </div>
  );
};
