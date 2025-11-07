import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={({ route }) => ({
        headerShown: false,
        lazy: false, // Preload all tabs immediately
        tabBarStyle: {
          backgroundColor: '#050505',
          borderTopColor: '#111111',
        },
        tabBarActiveTintColor: '#9b5cff',
        tabBarInactiveTintColor: '#777777',
        tabBarIcon: ({ color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap = 'home';
          if (route.name === 'swipe') iconName = 'flame';
          if (route.name === 'watchlist') iconName = 'list';
          if (route.name === 'profile') iconName = 'analytics';
          return <Ionicons name={iconName} size={size} color={color} />;
        },
      })}
    >
      <Tabs.Screen name="swipe" options={{ title: 'Swipe' }} />
      <Tabs.Screen name="watchlist" options={{ title: 'Watchlist' }} />
      <Tabs.Screen name="profile" options={{ title: 'Profile' }} />
    </Tabs>
  );
}
