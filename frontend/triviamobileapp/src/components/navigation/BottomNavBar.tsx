import React from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';
import { Device } from '../../utils/device';
import NavIcon from './NavIcon';

type NavItemType = 'home' | 'packs' | 'create' | 'friends' | 'profile';

// Define the navigation items
interface NavItemProps {
  id: NavItemType;
  label: string;
}

interface BottomNavBarProps {
  activeItemId: NavItemType;
  onItemPress: (itemId: NavItemType) => void;
}

const navItems: NavItemProps[] = [
  { id: 'home', label: 'Home' },
  { id: 'packs', label: 'Packs' },
  { id: 'create', label: 'Create' },
  { id: 'friends', label: 'Friends' },
  { id: 'profile', label: 'Profile' },
];

const BottomNavBar: React.FC<BottomNavBarProps> = ({
  activeItemId,
  onItemPress,
}) => {
  return (
    <View style={styles.container}>
      {navItems.map((item) => (
        <TouchableOpacity
          key={item.id}
          style={styles.navItem}
          onPress={() => onItemPress(item.id)}
          activeOpacity={0.7}
        >
          <NavIcon type={item.id} active={activeItemId === item.id} />
          <Typography
            variant="caption"
            color={activeItemId === item.id ? colors.primary.main : colors.text.secondary}
            style={activeItemId === item.id ? styles.activeLabel : undefined}
          >
            {item.label}
          </Typography>
          {activeItemId === item.id && <View style={styles.activeDot} />}
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: colors.background.default,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
    paddingBottom: Device.os.isIphoneX() ? 24 : 10,
    paddingTop: 10,
  },
  navItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    paddingVertical: 6,
  },
  activeLabel: {
    fontWeight: '500',
  },
  activeDot: {
    position: 'absolute',
    top: 0,
    width: 4,
    height: 4,
    backgroundColor: colors.primary.main,
    borderRadius: 2,
  },
});

export default BottomNavBar;