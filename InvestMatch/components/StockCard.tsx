import React, { useState } from 'react';
import { View, Text, StyleSheet, Pressable, Image } from 'react-native';

// Type definitions
export type Executive = {
  name: string;
  title: string;
  photoUrl?: string;
};

export type ChartPoint = {
  date: string;
  close: number;
};

export type Stock = {
  id: number;
  ticker: string;
  name: string;
  sector?: string;
  industry?: string;
  description?: string;
  summaryAi?: string;
  logoUrl?: string;
  marketCap?: number;
  currentPrice?: number;
  priceChangePct?: number;
  priceChangeAbs?: number;
  peRatio?: number;
  dividendYield?: number;
  profitMargin?: number;
  executives: Executive[];
  chartData?: ChartPoint[];
};

interface StockCardProps {
  stock: Stock;
}

// Utility functions
const formatMarketCap = (value?: number): string => {
  if (!value) return 'N/A';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
};

const formatPrice = (price?: number): string => {
  if (!price) return 'N/A';
  return `$${price.toFixed(2)}`;
};

const formatPercent = (value?: number): string => {
  if (value === undefined || value === null) return 'N/A';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};

const formatChange = (value?: number): string => {
  if (value === undefined || value === null) return 'N/A';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}`;
};

export function summarizeDescription(raw?: string, maxChars: number = 500): string {
  if (!raw) return 'No description available.';
  const cleaned = raw.replace(/\s+/g, ' ').trim();
  if (cleaned.length <= maxChars) return cleaned;
  return `${cleaned.slice(0, maxChars).trimEnd()}...`;
}

// TODO: Replace summarizeDescription with a call to a Supabase Edge Function that returns an AI-generated summary.

// Slide Components
const OverviewSlide: React.FC<{ stock: Stock }> = ({ stock }) => {
  const priceColor = (stock.priceChangePct ?? 0) >= 0 ? styles.positive : styles.negative;
  const sectorIndustry = [stock.sector, stock.industry].filter(Boolean).join(' / ');

  return (
    <View style={styles.slide}>
      <View style={styles.slideContent}>
        {/* Logo */}
        {stock.logoUrl ? (
          <Image
            source={{ uri: stock.logoUrl }}
            style={styles.logo}
            resizeMode="contain"
          />
        ) : (
          <View style={styles.initialAvatar}>
            <Text style={styles.initialAvatarText}>
              {stock.ticker?.[0]?.toUpperCase() ?? '?'}
            </Text>
          </View>
        )}

        {/* Ticker & Name */}
        <Text style={styles.ticker}>{stock.ticker}</Text>
        <Text style={styles.companyName}>{stock.name}</Text>

        {/* Sector & Industry */}
        {(stock.sector || stock.industry) && (
          <Text style={styles.sectorIndustry}>
            {[stock.sector, stock.industry].filter(Boolean).join(' / ')}
          </Text>
        )}

        {/* Price Info */}
        <View style={styles.priceContainer}>
          <Text style={styles.price}>{formatPrice(stock.currentPrice)}</Text>
          <View style={styles.priceChangeRow}>
            <Text style={[styles.priceChange, priceColor]}>
              {formatPercent(stock.priceChangePct)}
            </Text>
            <Text style={[styles.priceChange, priceColor]}>
              {formatChange(stock.priceChangeAbs)}
            </Text>
          </View>
        </View>

        {/* Market Cap */}
        <View style={styles.marketCapContainer}>
          <Text style={styles.label}>Market Cap</Text>
          <Text style={styles.marketCap}>{formatMarketCap(stock.marketCap)}</Text>
        </View>
      </View>
    </View>
  );
};

const AboutSlide: React.FC<{ stock: Stock }> = ({ stock }) => {
  // Use AI-generated summary if available, otherwise fallback to description
  const summary = stock.summaryAi || summarizeDescription(stock.description);

  return (
    <View style={styles.slide}>
      <View style={styles.slideContent}>
        <Text style={styles.slideTitle}>About {stock.name}</Text>
        <Text style={styles.aboutBody}>{summary}</Text>
      </View>
    </View>
  );
};

const PerformanceSlide: React.FC<{ stock: Stock }> = ({ stock }) => {
  const hasChartData = Boolean(stock.chartData && stock.chartData.length > 0);

  if (hasChartData) {
    console.log(`Chart data ready for ${stock.ticker}`, stock.chartData);
  }

  return (
    <View style={styles.slide}>
      <View style={styles.slideContent}>
        <Text style={styles.slideTitle}>1 Year Performance</Text>
        {hasChartData ? (
          <View style={styles.chartPlaceholder}>
            <Text style={styles.chartPlaceholderText}>
              Chart data connected ({stock.chartData!.length} points)
            </Text>
          </View>
        ) : (
          <View style={styles.chartPlaceholder}>
            <Text style={styles.chartPlaceholderText}>Chart coming soon</Text>
          </View>
        )}
        <View style={styles.financialStats}>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>P/E Ratio</Text>
            <Text style={styles.statValue}>
              {stock.peRatio !== undefined ? stock.peRatio.toFixed(2) : 'N/A'}
            </Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Dividend Yield</Text>
            <Text style={styles.statValue}>
              {stock.dividendYield !== undefined ? `${stock.dividendYield.toFixed(2)}%` : 'N/A'}
            </Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Profit Margin</Text>
            <Text style={styles.statValue}>
              {stock.profitMargin !== undefined ? `${stock.profitMargin.toFixed(2)}%` : 'N/A'}
            </Text>
          </View>
        </View>
      </View>
    </View>
  );
};

// Main Component
const StockCard: React.FC<StockCardProps> = ({ stock }) => {
  const slides = ['OVERVIEW', 'PERFORMANCE', 'ABOUT'] as const;
  type SlideKey = (typeof slides)[number];

  const [slideIndex, setSlideIndex] = useState(0);
  const currentSlide: SlideKey = slides[slideIndex];

  // Navigation functions
  const goPrev = () => {
    setSlideIndex((i) => Math.max(0, i - 1));
  };

  const goNext = () => {
    setSlideIndex((i) => Math.min(slides.length - 1, i + 1));
  };

  // Render current slide based on index
  const renderSlide = (slide: SlideKey) => {
    switch (slide) {
      case 'OVERVIEW':
        return <OverviewSlide stock={stock} />;
      case 'PERFORMANCE':
        return <PerformanceSlide stock={stock} />;
      case 'ABOUT':
        return <AboutSlide stock={stock} />;
      default:
        return <OverviewSlide stock={stock} />;
    }
  };

  return (
    <View style={styles.card}>
      {/* Slide content */}
      <View style={styles.slideContainer}>
        {renderSlide(currentSlide)}
      </View>

      {/* Tap areas for navigation */}
      <View style={styles.tapAreas}>
        {/* Left tap area - go to previous slide */}
        <Pressable
          style={styles.tapAreaLeft}
          onPress={goPrev}
          disabled={slideIndex === 0}
        >
          <View style={styles.tapAreaContent} />
        </Pressable>

        {/* Right tap area - go to next slide */}
        <Pressable
          style={styles.tapAreaRight}
          onPress={goNext}
          disabled={slideIndex === slides.length - 1}
        >
          <View style={styles.tapAreaContent} />
        </Pressable>
      </View>

      {/* Pagination Dots */}
      <View style={styles.pagination}>
        {slides.map((_, index) => (
          <View
            key={index}
            style={[styles.dot, index === slideIndex && styles.activeDot]}
          />
        ))}
      </View>
    </View>
  );
};

// Styles
const styles = StyleSheet.create({
  card: {
    height: '100%',
    backgroundColor: '#1a1a1a',
    borderRadius: 28,
    paddingHorizontal: 24,
    paddingVertical: 24,
    justifyContent: 'space-between',
    alignSelf: 'stretch',
    width: '100%',
    // Shadow for iOS
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 8,
    },
    shadowOpacity: 0.6,
    shadowRadius: 16,
    // Elevation for Android
    elevation: 12,
  },
  slideContainer: {
    flex: 1,
  },
  slide: {
    flex: 1,
    width: '100%',
    justifyContent: 'center',
  },
  tapAreas: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 60,
    flexDirection: 'row',
  },
  tapAreaLeft: {
    flex: 1,
  },
  tapAreaRight: {
    flex: 1,
  },
  tapAreaContent: {
    flex: 1,
  },
  slideContent: {
    flex: 1,
    justifyContent: 'center',
  },
  slideTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 20,
  },

  // Overview Slide
  logo: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignSelf: 'center',
    marginBottom: 16,
  },
  initialAvatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#2a2a2a',
    alignSelf: 'center',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  initialAvatarText: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '700',
  },
  ticker: {
    fontSize: 48,
    fontWeight: '800',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 4,
  },
  companyName: {
    fontSize: 18,
    fontWeight: '500',
    color: '#aaa',
    textAlign: 'center',
    marginBottom: 8,
  },
  sectorIndustry: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  priceContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  price: {
    fontSize: 36,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 8,
  },
  priceChangeRow: {
    flexDirection: 'row',
    gap: 12,
  },
  priceChange: {
    fontSize: 18,
    fontWeight: '600',
  },
  positive: {
    color: '#00C853',
  },
  negative: {
    color: '#FF3B30',
  },
  marketCapContainer: {
    alignItems: 'center',
  },
  label: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  marketCap: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
  },

  // About Slide
  aboutBody: {
    fontSize: 16,
    lineHeight: 24,
    color: '#ccc',
  },

  // Performance Slide
  chartPlaceholder: {
    height: 200,
    backgroundColor: '#0f0f0f',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  chartPlaceholderText: {
    fontSize: 16,
    color: '#555',
  },
  financialStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  statItem: {
    flex: 1,
    backgroundColor: '#0f0f0f',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
    textAlign: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },

  // Common
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    fontStyle: 'italic',
  },

  // Pagination
  pagination: {
    position: 'absolute',
    bottom: 16,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#333',
  },
  activeDot: {
    backgroundColor: '#fff',
    width: 24,
  },
});

export default StockCard;
