import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { Stock } from '@/components/StockCard';

interface UseStocksResult {
  stocks: Stock[];
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch stocks from Supabase
 * Returns loading state, stock data, error, and refetch function
 */
export function useStocks(): UseStocksResult {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchStocks = async () => {
    try {
      setLoading(true);
      setError(null);

      const { data, error: fetchError } = await supabase
        .from('stocks')
        .select('*')
        .order('ticker', { ascending: true });

      if (fetchError) {
        throw fetchError;
      }

      // Transform Supabase data to match Stock interface
      const transformedStocks: Stock[] = (data || []).map((stock) => ({
        id: stock.id,
        ticker: stock.ticker || '',
        name: stock.name || '',
        sector: stock.sector || undefined,
        industry: stock.industry || undefined,
        logoUrl: stock.logo_url || undefined,
        currentPrice: stock.current_price || undefined,
        priceChangePct: stock.price_change_pct || undefined,
        priceChangeAbs: stock.price_change_abs || undefined,
        marketCap: stock.market_cap || undefined,
        description: stock.description || undefined,
        peRatio: stock.pe_ratio || undefined,
        dividendYield: stock.dividend_yield || undefined,
        profitMargin: stock.profit_margin || undefined,
        executives: stock.executives || undefined,
        news: stock.news || undefined,
      }));

      setStocks(transformedStocks);
      console.log(`[useStocks] Fetched ${transformedStocks.length} stocks from Supabase`);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch stocks');
      setError(error);
      console.error('[useStocks] Error fetching stocks:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStocks();
  }, []);

  return {
    stocks,
    loading,
    error,
    refetch: fetchStocks,
  };
}
