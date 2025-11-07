import { useEffect, useState } from 'react';
import { ActivityIndicator, View, Text, StyleSheet } from 'react-native';
import Swiper from 'react-native-deck-swiper';

import { supabase } from '../../lib/supabaseClient';
import { useAuth } from '../../lib/AuthContext';
import StockCard, { Stock, ChartPoint } from '../../components/StockCard';

type StockRow = {
  id: number;
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  description: string | null;
  summary_ai: string | null;
  market_cap: number | null;
  logo_url: string | null;
  current_price: number | null;
  price_change_pct: number | null;
  price_change_usd: number | null;
  pe_ratio: number | null;
  dividend_yield: number | null;
  profit_margin: number | null;
  chart_image_url: string | null;
  // chart_data_json will be added when backend populates it
};

function mapRowToStock(row: StockRow): Stock {
  return {
    id: row.id,
    ticker: row.ticker,
    name: row.name,
    sector: row.sector || undefined,
    industry: row.industry || undefined,
    description: row.description || undefined,
    summaryAi: row.summary_ai || undefined,
    logoUrl: row.logo_url || undefined,
    marketCap: row.market_cap ?? undefined,
    currentPrice: row.current_price ?? undefined,
    priceChangePct: row.price_change_pct ?? undefined,
    priceChangeAbs: row.price_change_usd ?? undefined,
    peRatio: row.pe_ratio ?? undefined,
    dividendYield: row.dividend_yield ?? undefined,
    profitMargin: row.profit_margin ?? undefined,
    chartImageUrl: row.chart_image_url || undefined,
    executives: [],
    chartData: undefined, // Will be populated when backend adds chart_data_json column
  };
}

export default function SwipeScreen() {
  const { user } = useAuth();
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStocks = async () => {
      if (!user) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // First, get stocks the user has already swiped on
        const { data: swipedStocks, error: swipeError } = await supabase
          .from('user_swipes')
          .select('company_id')
          .eq('user_id', user.id);

        if (swipeError) {
          console.error('Error loading swiped stocks:', swipeError);
        }

        const swipedIds = swipedStocks?.map((s) => s.company_id) || [];
        console.log(`User has already swiped on ${swipedIds.length} stocks`);

        // Load stocks, excluding already-swiped ones
        let query = supabase
          .from('stocks')
          .select(
            'id, ticker, name, sector, industry, description, summary_ai, market_cap, logo_url, current_price, price_change_pct, price_change_usd, pe_ratio, dividend_yield, profit_margin, chart_image_url'
          )
          .order('market_cap', { ascending: false });

        // Filter out already-swiped stocks
        if (swipedIds.length > 0) {
          query = query.not('id', 'in', `(${swipedIds.join(',')})`);
        }

        const { data, error } = await query.limit(60);

        if (error) {
          console.error('Supabase error loading stocks:', error);
          setError('Failed to load stocks');
          setStocks([]);
          return;
        }

        if (data) {
          const typed = data as StockRow[];
          // Shuffle the stocks for variety
          const shuffled = typed.sort(() => Math.random() - 0.5);
          const mapped = shuffled.map(mapRowToStock);
          setStocks(mapped);
          console.log(`Loaded ${mapped.length} new stocks (${swipedIds.length} already swiped)`);
        }
      } catch (e) {
        console.error('Unexpected error loading stocks:', e);
        setError('Unexpected error loading stocks');
        setStocks([]);
      } finally {
        setLoading(false);
      }
    };

    loadStocks();
  }, [user]);

  // Record swipe to database
  const recordSwipe = async (stockId: number, direction: 'left' | 'right') => {
    if (!user) {
      console.error('No user logged in');
      return;
    }

    try {
      const { error } = await supabase.from('user_swipes').insert({
        user_id: user.id,
        company_id: stockId,
        swipe_direction: direction,
      });

      if (error) {
        // Ignore duplicate key errors (stock already swiped)
        if (error.code === '23505') {
          console.log(`Already swiped on stock ${stockId}, skipping`);
        } else {
          console.error('Error recording swipe:', error);
        }
      } else {
        console.log(`✅ Recorded ${direction} swipe for stock ${stockId}`);
      }
    } catch (e) {
      console.error('Unexpected error recording swipe:', e);
    }
  };

  // Add to watchlist (for right swipes)
  const addToWatchlist = async (stockId: number, stockTicker: string) => {
    if (!user) {
      console.error('No user logged in');
      return;
    }

    try {
      const { error } = await supabase.from('user_watchlist').insert({
        user_id: user.id,
        company_id: stockId,
        notes: `Added ${stockTicker} from swipe`,
      });

      if (error) {
        // Ignore duplicate key errors (already in watchlist)
        if (error.code === '23505') {
          console.log(`${stockTicker} already in watchlist, skipping`);
        } else {
          console.error('Error adding to watchlist:', error);
        }
      } else {
        console.log(`⭐ Added ${stockTicker} to watchlist`);
      }
    } catch (e) {
      console.error('Unexpected error adding to watchlist:', e);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#fff" />
      </View>
    );
  }

  if (error || stocks.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={{ color: '#fff', textAlign: 'center' }}>
          {error ?? 'No stocks available. Please try again later.'}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <View style={styles.swiperWrapper}>
        <Swiper
          cards={stocks}
          renderCard={(card) => (card ? <StockCard stock={card} /> : null)}
          backgroundColor="transparent"
          stackSize={3}
          stackSeparation={20}
          cardHorizontalMargin={20}
          cardVerticalMargin={80}
          disableTopSwipe
          disableBottomSwipe
          verticalSwipe={false}
          horizontalSwipe
          infinite={false}
          showSecondCard={true}
          animateOverlayLabelsOpacity
          overlayLabels={{
            left: {
              title: 'PASS',
              style: {
                label: {
                  backgroundColor: '#FF3B30',
                  color: '#fff',
                  fontSize: 24,
                  fontWeight: 'bold',
                  padding: 10,
                  borderRadius: 8,
                },
                wrapper: {
                  flexDirection: 'column',
                  alignItems: 'flex-end',
                  justifyContent: 'flex-start',
                  marginTop: 30,
                  marginLeft: -30,
                },
              },
            },
            right: {
              title: 'LIKE',
              style: {
                label: {
                  backgroundColor: '#00C853',
                  color: '#fff',
                  fontSize: 24,
                  fontWeight: 'bold',
                  padding: 10,
                  borderRadius: 8,
                },
                wrapper: {
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  justifyContent: 'flex-start',
                  marginTop: 30,
                  marginLeft: 30,
                },
              },
            },
          }}
          onSwipedRight={async (index) => {
            const stock = stocks[index];
            console.log('Liked', stock?.ticker);
            await recordSwipe(stock.id, 'right');
            await addToWatchlist(stock.id, stock.ticker);
          }}
          onSwipedLeft={async (index) => {
            const stock = stocks[index];
            console.log('Passed', stock?.ticker);
            await recordSwipe(stock.id, 'left');
          }}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#000',
  },
  swiperWrapper: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 0,
    paddingTop: 40,
    paddingBottom: 80,
  },
  center: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
});
