Component Features
5 Swipeable Slides:
Overview - Logo, ticker, company name, sector/industry, price info, market cap
Description - About section with company description
Leadership - Up to 4 executives with photos/initials, names, and titles
Recent News - Up to 3 news items with title and source
Chart & Financials - Placeholder chart + P/E ratio, dividend yield, profit margin
Key Features:
Horizontal FlatList with pagingEnabled for smooth Tinder-like swiping
Pagination dots at bottom showing active slide
Dark theme (#111 background) with white/gray text
Green/red color coding for positive/negative price changes
Circular photos with fallback initials
Clean, minimal typography optimized for readability
TypeScript interfaces exported for reusability
Utility functions for formatting prices, percentages, market cap

import StockCard from '@/components/StockCard';

// In your component:
const mockStock = {
  id: '1',
  ticker: 'AAPL',
  name: 'Apple Inc.',
  sector: 'Technology',
  industry: 'Consumer Electronics',
  logoUrl: 'https://example.com/apple-logo.png',
  currentPrice: 178.45,
  priceChangePct: 2.34,
  priceChangeAbs: 4.12,
  marketCap: 2800000000000,
  description: 'Apple Inc. designs, manufactures, and markets smartphones...',
  peRatio: 28.5,
  dividendYield: 0.52,
  profitMargin: 25.3,
  executives: [
    { id: '1', name: 'Tim Cook', title: 'CEO', photoUrl: '...' },
    { id: '2', name: 'Luca Maestri', title: 'CFO' },
  ],
  news: [
    { id: '1', title: 'Apple announces new product line', source: 'Reuters' },
    { id: '2', title: 'Record quarterly earnings reported', source: 'Bloomberg' },
  ],
};

return <StockCard stock={mockStock} />;

Swiper Configuration
react-native-deck-swiper with 8 mock stocks (AAPL, TSLA, MSFT, NVDA, AMZN, GOOGL, META, JPM)
Black background (#000000)
Stack size of 3 cards
Top/bottom swipe disabled (horizontal only)
Card opacity animation enabled
Overlay labels showing "LIKE" (green) and "PASS" (red) during swipes
Swipe Handlers
Right swipe → console.log("Liked", ticker)
Left swipe → console.log("Passed", ticker)
All swiped → console.log("All cards swiped!")
UI Elements
Header with title and instructions
Footer showing stock count
Each card renders the full StockCard component with 5 swipeable slides

Migrating to Supabase Later
When you're ready to replace mock data with real data from Supabase:
Create a Supabase table (e.g., stocks) with columns matching the Stock interface
Add a data fetching hook (e.g., hooks/useStocks.ts):
const { data: stocks, loading } = useStocks();
Replace mockStocks with fetched data:
// Replace line 7:
const mockStocks: Stock[] = [...]; 

// With:
const { stocks, loading } = useStocks();
if (loading) return <LoadingSpinner />;
Track swipe actions in Supabase:
const handleSwipedRight = async (index: number) => {
  await supabase.from('user_swipes').insert({
    user_id: currentUserId,
    stock_id: stocks[index].id,
    action: 'like'
  });
};
The component structure is ready for this migration - you'll just need to swap the data source!


