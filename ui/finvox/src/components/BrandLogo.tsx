import React from 'react';
import { TrendingUp } from 'lucide-react';

interface BrandLogoProps {
  size?: 'small' | 'medium' | 'large';
  color?: 'dark' | 'light';
}

const BrandLogo: React.FC<BrandLogoProps> = ({ size = 'medium', color = 'dark' }) => {
  // Size configurations
  const sizes = {
    small: {
      iconSize: 18,
      boxSize: '32px',
      fontSize: '1.2rem',
      gap: '0.4rem',
      borderRadius: '8px',
      iconPadding: '6px'
    },
    medium: {
      iconSize: 22,
      boxSize: '40px',
      fontSize: '1.45rem',
      gap: '0.5rem',
      borderRadius: '10px',
      iconPadding: '8px'
    },
    large: {
      iconSize: 28,
      boxSize: '52px',
      fontSize: '1.8rem',
      gap: '0.7rem',
      borderRadius: '14px',
      iconPadding: '12px'
    }
  };

  const currentSize = sizes[size];
  const textColor = color === 'dark' ? '#0a0f1e' : '#ffffff';

  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: currentSize.gap,
      fontWeight: 800,
      fontSize: currentSize.fontSize,
      color: textColor,
      letterSpacing: '-0.02em'
    }}>
      <div style={{ 
        background: 'linear-gradient(135deg, #e11d48, #fb7185)', 
        width: currentSize.boxSize,
        height: currentSize.boxSize,
        borderRadius: currentSize.borderRadius, 
        color: 'white', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        flexShrink: 0,
        boxShadow: '0 4px 14px -4px rgba(225, 29, 72, 0.4)'
      }}>
        <TrendingUp size={currentSize.iconSize} strokeWidth={2.5} />
      </div>
      FinVox
    </div>
  );
};

export default BrandLogo;
