import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, ActivityIndicator, Pressable, Alert } from 'react-native';
import { supabase } from '../../lib/supabaseClient';
import { useAuth } from '../../lib/AuthContext';

type WatchlistItem = {
  id: number;
  company_id: number;
  notes: string | null;
  added_at: string;
  stocks: {
    ticker: string;
    name: string;
    current_price: number | null;
    price_change_pct: number | null;
    market_cap: number | null;
    sector: string | null;
  };
};

export default function WatchlistScreen() {
  const { user } = useAuth();
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadWatchlist = async () => {
    if (!user) {
      console.error('No user logged in');
      return;
    }

    try {
      const { data, error } = await supabase
        .from('user_watchlist')
        .select(`
          id,
          company_id,
          notes,
          added_at,
          stocks (
            ticker,
            name,
            current_price,
            price_change_pct,
            market_cap,
            sector
          )
        `)
        .eq('user_id', user.id)
        .order('added_at', { ascending: false });

      if (error) {
        console.error('Error loading watchlist:', error);
      } else {
        // Map the data to ensure correct structure (stocks is a single object, not array)
        const mappedData = (data || []).map((item: any) => ({
          ...item,
          stocks: Array.isArray(item.stocks) ? item.stocks[0] : item.stocks,
        }));
        setWatchlist(mappedData);
        console.log(`Loaded ${data?.length || 0} watchlist items`);
      }
    } catch (e) {
      console.error('Unexpected error loading watchlist:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadWatchlist();
  }, [user]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadWatchlist();
  };

  const handleRemove = (itemId: number, ticker: string, companyId: number) => {
    Alert.alert(
      'Remove from Watchlist',
      `Remove ${ticker} from your watchlist? This will allow it to reappear in your feed.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            if (!user) return;

            try {
              console.log(`Removing ${ticker} from watchlist and swipe history...`);

              // Delete from watchlist
              const { error: watchlistError } = await supabase
                .from('user_watchlist')
                .delete()
                .eq('id', itemId);

              if (watchlistError) {
                console.error('Error removing from watchlist:', watchlistError);
                Alert.alert('Error', 'Failed to remove from watchlist');
                return;
              }

              // Delete the swipe record so it can reappear in feed
              const { error: swipeError } = await supabase
                .from('user_swipes')
                .delete()
                .eq('user_id', user.id)
                .eq('company_id', companyId);

              if (swipeError) {
                console.error('Error removing swipe record:', swipeError);
                // Don't show error to user - watchlist removal succeeded
              }

              console.log(`✅ Removed ${ticker} from watchlist and swipe history`);
              console.log(`   ${ticker} will reappear in your feed`);
              setWatchlist((prev) => prev.filter((item) => item.id !== itemId));
            } catch (e) {
              console.error('Unexpected error:', e);
            }
          },
        },
      ]
    );
  };

  const renderItem = ({ item }: { item: WatchlistItem }) => {
    const stock = item.stocks;
    const priceChangeColor = (stock.price_change_pct ?? 0) >= 0 ? '#00C853' : '#FF3B30';

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.stockInfo}>
            <Text style={styles.ticker}>{stock.ticker}</Text>
            <Text style={styles.name} numberOfLines={1}>{stock.name}</Text>
            {stock.sector && (
              <Text style={styles.sector}>{stock.sector}</Text>
            )}
          </View>
          <Pressable
            style={styles.removeButton}
            onPress={() => handleRemove(item.id, stock.ticker, item.company_id)}
          >
            <Text style={styles.removeButtonText}>✕</Text>
          </Pressable>
        </View>

        <View style={styles.cardBody}>
          {stock.current_price && (
            <View style={styles.priceRow}>
              <Text style={styles.price}>${stock.current_price.toFixed(2)}</Text>
              {stock.price_change_pct !== null && (
                <Text style={[styles.priceChange, { color: priceChangeColor }]}>
                  {stock.price_change_pct >= 0 ? '+' : ''}
                  {stock.price_change_pct.toFixed(2)}%
                </Text>
              )}
            </View>
          )}

          {stock.market_cap && (
            <Text style={styles.marketCap}>
              Market Cap: ${(stock.market_cap / 1e9).toFixed(2)}B
            </Text>
          )}

          {item.notes && (
            <Text style={styles.notes} numberOfLines={2}>
              {item.notes}
            </Text>
          )}
        </View>

        <Text style={styles.date}>
          Added {new Date(item.added_at).toLocaleDateString()}
        </Text>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#00C853" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>My Watchlist</Text>
        <Text style={styles.headerSubtitle}>
          {watchlist.length} {watchlist.length === 1 ? 'stock' : 'stocks'}
        </Text>
      </View>

      {watchlist.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>⭐</Text>
          <Text style={styles.emptyTitle}>Your watchlist is empty</Text>
          <Text style={styles.emptyText}>
            Swipe right on stocks you like to add them to your watchlist
          </Text>
        </View>
      ) : (
        <FlatList
          data={watchlist}
          renderItem={renderItem}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          refreshing={refreshing}
          onRefresh={handleRefresh}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  center: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    paddingTop: 60,
    paddingHorizontal: 24,
    paddingBottom: 24,
    backgroundColor: '#000',
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: '800',
    color: '#fff',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#666',
  },
  listContent: {
    paddingHorizontal: 24,
    paddingBottom: 24,
  },
  card: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  stockInfo: {
    flex: 1,
  },
  ticker: {
    fontSize: 24,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 4,
  },
  name: {
    fontSize: 14,
    color: '#aaa',
    marginBottom: 8,
  },
  sector: {
    fontSize: 12,
    color: '#666',
    textTransform: 'uppercase',
  },
  removeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeButtonText: {
    color: '#FF3B30',
    fontSize: 18,
    fontWeight: '700',
  },
  cardBody: {
    marginBottom: 12,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 8,
  },
  price: {
    fontSize: 28,
    fontWeight: '700',
    color: '#fff',
    marginRight: 12,
  },
  priceChange: {
    fontSize: 16,
    fontWeight: '600',
  },
  marketCap: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  notes: {
    fontSize: 14,
    color: '#aaa',
    fontStyle: 'italic',
    marginTop: 8,
  },
  date: {
    fontSize: 12,
    color: '#666',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 48,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
  },
});
