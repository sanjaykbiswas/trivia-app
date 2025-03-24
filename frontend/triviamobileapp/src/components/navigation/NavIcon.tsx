import React from 'react';
import Svg, { Path, Rect, Circle, Polyline, Line } from 'react-native-svg';
import { colors } from '../../theme';

type IconType = 'home' | 'packs' | 'create' | 'friends' | 'profile';

interface NavIconProps {
  type: IconType;
  size?: number;
  color?: string;
  active?: boolean;
}

const NavIcon: React.FC<NavIconProps> = ({
  type,
  size = 24,
  color,
  active = false
}) => {
  const iconColor = color || (active ? colors.primary.main : colors.text.secondary);
  const opacity = active ? 1 : 0.5;

  // Render different SVG paths based on the icon type
  const renderIcon = () => {
    switch (type) {
      case 'home':
        return (
          <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity={opacity}>
            <Path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            <Polyline points="9 22 9 12 15 12 15 22" />
          </Svg>
        );
      case 'packs':
        return (
          <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity={opacity}>
            <Rect x="2" y="5" width="16" height="16" rx="2" ry="2" />
            <Rect x="6" y="3" width="16" height="16" rx="2" ry="2" />
          </Svg>
        );
      case 'create':
        return (
          <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity={opacity}>
            <Line x1="18" y1="2" x2="22" y2="6" />
            <Path d="M7.5 20.5L19 9l-4-4L3.5 16.5 2 22l5.5-1.5z" />
          </Svg>
        );
      case 'friends':
        return (
          <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity={opacity}>
            <Path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <Circle cx="9" cy="7" r="4" />
            <Path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <Path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </Svg>
        );
      case 'profile':
        return (
          <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity={opacity}>
            <Path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <Circle cx="12" cy="7" r="4" />
          </Svg>
        );
      default:
        return null;
    }
  };

  return renderIcon();
};

export default NavIcon;