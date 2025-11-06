# Usage Examples for InvestMatch

## Using `useUserId` Hook in Swipe Screen

The `useUserId` hook generates and persists an anonymous user ID for tracking user actions without authentication.

### Basic Usage in `(tabs)/swipe.tsx`

```typescript
import { useUserId } from '@/hooks/useUserId';

export default function SwipeScreen() {
  const userId = useUserId();
  const swiperRef = useRef<Swiper<Stock>>(null);

  // Wait for userId to load before tracking actions
  const handleSwipedRight = (index: number) => {
    const stock = mockStocks[index];
    console.log('Liked', stock.ticker);

    if (userId) {
      // Ready to track swipe in database
      // Example: await supabase.from('swipes').insert({
      //   user_id: userId,
      //   stock_id: stock.id,
      //   action: 'like',
      //   created_at: new Date().toISOString()
      // });
    }
  };

  const handleSwipedLeft = (index: number) => {
    const stock = mockStocks[index];
    console.log('Passed', stock.ticker);

    if (userId) {
      // Ready to track swipe in database
      // Example: await supabase.from('swipes').insert({
      //   user_id: userId,
      //   stock_id: stock.id,
      //   action: 'pass',
      //   created_at: new Date().toISOString()
      // });
    }
  };

  // Show loading state while userId initializes
  if (!userId) {
    return (
      <View style={styles.container}>
        <Text style={styles.headerText}>Loading...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Your swiper UI */}
    </View>
  );
}
```

### Advanced: Using with Supabase

```typescript
import { useUserId } from '@/hooks/useUserId';
import { supabase } from '@/lib/supabase';

export default function SwipeScreen() {
  const userId = useUserId();

  const trackSwipe = async (stockId: string, action: 'like' | 'pass') => {
    if (!userId) {
      console.warn('User ID not loaded yet');
      return;
    }

    try {
      const { error } = await supabase
        .from('user_swipes')
        .insert({
          user_id: userId,
          stock_id: stockId,
          action: action,
          created_at: new Date().toISOString(),
        });

      if (error) throw error;

      console.log(`Successfully tracked ${action} for stock ${stockId}`);
    } catch (error) {
      console.error('Error tracking swipe:', error);
    }
  };

  const handleSwipedRight = (index: number) => {
    const stock = mockStocks[index];
    trackSwipe(stock.id.toString(), 'like');
  };

  const handleSwipedLeft = (index: number) => {
    const stock = mockStocks[index];
    trackSwipe(stock.id.toString(), 'pass');
  };

  // Rest of component...
}
```

### Utility Functions

The hook also exports utility functions for special cases:

```typescript
import { clearUserId, getUserId } from '@/hooks/useUserId';

// Clear the user ID (useful for testing or "reset" feature)
await clearUserId();

// Get user ID outside of React components
const userId = await getUserId();
```

## Key Points

1. **userId starts as `null`** while loading from AsyncStorage
2. **Check `if (userId)`** before using it for tracking
3. **Once generated, the ID persists** across app restarts
4. **Each device gets a unique ID** for anonymous tracking
5. **No authentication required** - perfect for MVP phase
