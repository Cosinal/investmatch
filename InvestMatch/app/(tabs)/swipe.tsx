import { useEffect, useState } from 'react';
import { ActivityIndicator, View, Text, StyleSheet } from 'react-native';
import Swiper from 'react-native-deck-swiper';

import { supabase } from '../../lib/supabaseClient';
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
    executives: [],
    chartData: undefined, // Will be populated when backend adds chart_data_json column
  };
}

export default function SwipeScreen() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStocks = async () => {
      try {
        setLoading(true);
        setError(null);

        const { data, error } = await supabase
          .from('stocks')
          .select(
            'id, ticker, name, sector, industry, description, summary_ai, market_cap, logo_url, current_price, price_change_pct, price_change_usd, pe_ratio, dividend_yield, profit_margin'
          )
          .order('market_cap', { ascending: false })
          .limit(60);

        if (error) {
          console.error('Supabase error loading stocks:', error);
          setError('Failed to load stocks');
          setStocks([]);
          return;
        }

        if (data) {
          const typed = data as StockRow[];
          const mapped = typed.map(mapRowToStock);
          setStocks(mapped);
          console.log(`Loaded ${mapped.length} stocks from Supabase`);
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
  }, []);

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
          onSwipedRight={(index) => {
            const stock = stocks[index];
            console.log('Liked', stock?.ticker);
            // Future: persist "liked" swipe to Supabase
          }}
          onSwipedLeft={(index) => {
            const stock = stocks[index];
            console.log('Passed', stock?.ticker);
            // Future: persist "passed" swipe to Supabase
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
