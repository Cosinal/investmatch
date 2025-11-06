import { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { v4 as uuidv4 } from 'uuid';
import 'react-native-get-random-values';

const USER_ID_KEY = 'investmatch_user_id';

/**
 * Custom hook that generates and persists an anonymous user ID per device.
 * Used for tracking swipes and watchlists without authentication.
 *
 * @returns {string | null} userId - The persistent user ID, or null while loading
 */
export function useUserId(): string | null {
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const initializeUserId = async () => {
      try {
        // Check if user ID already exists in storage
        const existingId = await AsyncStorage.getItem(USER_ID_KEY);

        if (existingId) {
          // Use existing ID
          setUserId(existingId);
        } else {
          // Generate new UUID
          const newId = uuidv4();

          // Persist to AsyncStorage
          await AsyncStorage.setItem(USER_ID_KEY, newId);

          // Update state
          setUserId(newId);

          console.log('[useUserId] Generated new anonymous user ID:', newId);
        }
      } catch (error) {
        console.error('[useUserId] Error initializing user ID:', error);
      }
    };

    initializeUserId();
  }, []);

  return userId;
}

/**
 * Utility function to manually clear the stored user ID (for testing/debugging)
 */
export async function clearUserId(): Promise<void> {
  try {
    await AsyncStorage.removeItem(USER_ID_KEY);
    console.log('[useUserId] User ID cleared');
  } catch (error) {
    console.error('[useUserId] Error clearing user ID:', error);
  }
}

/**
 * Utility function to get the user ID synchronously (if already loaded)
 */
export async function getUserId(): Promise<string | null> {
  try {
    return await AsyncStorage.getItem(USER_ID_KEY);
  } catch (error) {
    console.error('[useUserId] Error getting user ID:', error);
    return null;
  }
}
