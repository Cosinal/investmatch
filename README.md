# InvestMatch - Tinder for Investments

**Making investment discovery engaging for our generation, not homework-like.**

A mobile app that allows users to swipe through TSX stock opportunities with engaging, AI-generated summaries and real-time performance data.

---

## 📊 Project Status: MVP in Progress

### ✅ Completed (Backend & Data Infrastructure)

#### Database Architecture
- **Supabase PostgreSQL** as primary database
- **`stocks` table**: 60 TSX companies with metadata
  - Core fields: `id`, `ticker`, `name`
  - Performance metrics: `ytd_return`, `current_price`, `first_price_2025`
  - Visual assets: `chart_image_url`
  - Last updated: `price_updated_at`
- **`stock_prices` table**: Historical price data
  - 11,289+ daily closing prices (YTD 2025)
  - Unique constraint on `(company_id, date)`
  - Indexed for fast querying
- **Supabase Storage**: `stock-charts` bucket for chart images (public)

#### Data Pipeline (Python Scripts)
1. **`fetch_stock_prices.py`** ✅
   - Fetches YTD closing prices from Yahoo Finance
   - Handles 59/60 stocks successfully (CAR.UN excluded)
   - Batch upserts to `stock_prices` table
   - Runs incrementally (only adds new dates)

2. **`update_stock_metrics.py`** ✅
   - Calculates YTD return percentage for each stock
   - Updates `stocks` table with current metrics
   - Shows top/bottom performers
   - Provides performance summary

3. **`visualize_all_stocks.py`** ✅
   - Generates professional line charts for all 59 stocks
   - Color-coded: green (positive YTD), red (negative YTD)
   - High-resolution PNGs (150 DPI)
   - Saves to `charts/` directory

4. **`upload_charts_to_supabase.py`** ✅
   - Uploads all chart PNGs to Supabase Storage
   - Updates `stocks` table with public image URLs
   - Charts accessible via `chart_image_url` field

#### AI-Generated Content System
- Prompt designed for creating engaging 100-word investment pitches
- Converts lengthy company descriptions into "swipe-worthy" summaries
- Focuses on: hook, market position, growth opportunity
- Style: active language, scannable format, investor-focused

---

## 🚧 MVP Features - To Build

### Critical Path (Must Have for MVP)

#### 1. Frontend - Stock Card Swipe Interface
**Tech Stack**: React Native + Expo
**Status**: Not Started

**Components Needed**:
- `StockCard.tsx` - Main swipeable card component
  - Company name and ticker
  - AI-generated 100-word pitch
  - YTD performance badge (+X.X% in green/red)
  - Current price display
  - Chart image from Supabase Storage
  - Sector/industry tag

- `SwipeDeck.tsx` - Card stack manager
  - Tinder-style swipe mechanics
  - Like (swipe right) / Pass (swipe left)
  - Animation on swipe
  - Load next card from queue

- `StockChart.tsx` - Embedded chart display
  - Fetches `chart_image_url` from Supabase
  - Displays YTD line chart
  - Handles loading states

**API Integration**:
```javascript
// Fetch stock data
const { data: stocks } = await supabase
  .from('stocks')
  .select('*')
  .order('id');

// Display in swipe deck
```

---

#### 2. AI Content Generation - Company Summaries
**Status**: Prompt Ready, Execution Needed

**Task**: Run all 60 company descriptions through the AI prompt
- Input: Lengthy company descriptions (need to source these)
- Output: 100-word engaging summaries
- Storage: Add `ai_summary` column to `stocks` table

**SQL Change Needed**:
```sql
ALTER TABLE stocks 
ADD COLUMN IF NOT EXISTS ai_summary TEXT;
```

**Script to Create**: `generate_summaries.py`
- Read company descriptions (from where? Need data source)
- Call Claude API with prompt template
- Store results in `ai_summary` column

**Open Question**: Where are the original company descriptions?
- Manual input?
- Scrape from TSX website?
- Use Yahoo Finance company profiles?

---

#### 3. User Interaction Tracking
**Status**: Database Design Needed

**New Table**: `user_swipes`
```sql
CREATE TABLE user_swipes (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  company_id BIGINT REFERENCES stocks(id),
  swipe_direction TEXT CHECK (swipe_direction IN ('left', 'right')),
  swiped_at TIMESTAMP DEFAULT NOW()
);
```

**New Table**: `user_watchlist` (for "swiped right" stocks)
```sql
CREATE TABLE user_watchlist (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  company_id BIGINT REFERENCES stocks(id),
  added_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, company_id)
);
```

**Frontend Logic**:
- Swipe right → Add to watchlist + log swipe
- Swipe left → Log swipe only
- Watchlist screen to review saved stocks

---

#### 4. Authentication
**Status**: Not Started

**Implementation**: Supabase Auth
- Email/password signup
- Google OAuth (optional for MVP)
- Persist user sessions
- Link swipes/watchlist to user

**Components Needed**:
- `LoginScreen.tsx`
- `SignupScreen.tsx`
- Auth context/provider

---

### Nice-to-Have (Post-MVP)

#### 1. Daily Price Updates Automation
**Current State**: Manual script execution
**Future**: 
- GitHub Actions cron job (daily at 5:30 PM EST)
- OR Supabase Edge Function with cron trigger
- Automatically run: fetch → metrics → visualize → upload

#### 2. Advanced Filtering
- Filter by sector (e.g., "only show tech stocks")
- Filter by YTD performance (e.g., "> +10%")
- Filter by price range

#### 3. Stock Detail Page
- Full company information
- News feed integration
- Analyst ratings
- Peer comparison

#### 4. Portfolio Tracking
- Add holdings (# of shares owned)
- Track total portfolio value
- P&L calculations

#### 5. Social Features
- Share stocks with friends
- See what others are watching
- Discussion/comments

#### 6. Push Notifications
- Daily stock movers
- Watchlist price alerts
- New stock additions

---

## 🏗️ Technical Architecture

### Backend
- **Database**: Supabase (PostgreSQL)
- **Storage**: Supabase Storage (for chart images)
- **APIs**: Supabase REST API + Realtime subscriptions
- **Data Sources**: Yahoo Finance (via yfinance Python library)

### Frontend
- **Framework**: React Native + Expo
- **State Management**: React Context / Zustand (TBD)
- **Navigation**: React Navigation
- **Auth**: Supabase Auth
- **Styling**: Tailwind (via NativeWind) or styled-components (TBD)

### Data Flow
```
Yahoo Finance (yfinance) 
  → Python Scripts 
  → Supabase PostgreSQL 
  → Supabase Storage (charts)
  → React Native App
  → User Interactions
  → Supabase (swipes/watchlist)
```

---

## 📁 Current File Structure

```
apps/
├── fetch_stock_prices.py          # Fetch daily prices from Yahoo Finance
├── update_stock_metrics.py        # Calculate YTD metrics
├── visualize_all_stocks.py        # Generate all chart PNGs
├── upload_charts_to_supabase.py   # Upload charts to Storage
├── .env                           # Supabase credentials
├── requirements.txt               # Python dependencies
└── charts/                        # Local chart storage (59 PNGs)
    ├── SHOP_ytd_chart.png
    ├── RY_ytd_chart.png
    └── ...

investmatch-app/                   # React Native app (to be created)
├── src/
│   ├── components/
│   │   ├── StockCard.tsx
│   │   ├── SwipeDeck.tsx
│   │   └── StockChart.tsx
│   ├── screens/
│   │   ├── HomeScreen.tsx
│   │   ├── WatchlistScreen.tsx
│   │   └── LoginScreen.tsx
│   └── lib/
│       └── supabaseClient.ts
└── package.json
```

---

## 🔧 Setup & Development Workflow

### Initial Setup (Completed)
1. ✅ Created Supabase project
2. ✅ Set up `stocks` and `stock_prices` tables
3. ✅ Populated 60 TSX stocks
4. ✅ Fetched YTD price data (11,289 records)
5. ✅ Generated performance charts
6. ✅ Uploaded charts to Supabase Storage

### Daily Development Loop (Current)
```bash
# Update stock data (manual for now)
python fetch_stock_prices.py      # Fetch new prices
python update_stock_metrics.py    # Recalculate metrics
python visualize_all_stocks.py    # Regenerate charts
python upload_charts_to_supabase.py  # Update chart URLs
```

### React Native Development (To Start)
```bash
# Create new Expo project
npx create-expo-app investmatch-app --template blank-typescript

# Install dependencies
npm install @supabase/supabase-js
npm install react-native-gesture-handler react-native-reanimated

# Run on device
npm start
```

---

## 🎯 MVP Completion Checklist

### Data & Backend
- [x] Database schema designed and created
- [x] 60 TSX stocks populated
- [x] YTD price data collected (11,289 records)
- [x] Performance metrics calculated
- [x] Charts generated and uploaded
- [ ] AI summaries generated for all stocks
- [ ] User authentication tables created
- [ ] Swipe tracking tables created

### Frontend
- [ ] React Native project initialized
- [ ] Supabase client configured
- [ ] Stock card component built
- [ ] Swipe deck implemented
- [ ] Chart display working
- [ ] Authentication flow built
- [ ] Watchlist screen created

### Features
- [ ] User can swipe through stocks
- [ ] User can see YTD chart on each card
- [ ] User can read AI-generated summary
- [ ] Swipe right adds to watchlist
- [ ] Watchlist persists after app restart
- [ ] User can log in/out

---

## 🐛 Known Issues & Limitations

### Data Issues
1. **CAR.UN ticker** - Not fetching from Yahoo Finance
   - Tried: `CAR.UN.TO`, `CAR.TO`
   - Status: Excluded for now (59/60 stocks working)
   - Fix: Research correct ticker symbol or exclude permanently

2. **Market hours** - Data only updates when markets are open
   - Weekends/holidays show last trading day's close
   - Not a bug, just expected behavior

### Technical Debt
1. **No automated updates** - Scripts run manually
   - Need: Daily cron job or scheduled function
   
2. **No error alerting** - Script failures go unnoticed
   - Need: Email/Slack notifications on errors

3. **Chart regeneration** - All 59 charts regenerate each time
   - Optimization: Only regenerate charts with new data
   - Not critical for MVP

---

## 💰 Monetization Strategy (Post-MVP)

### Freemium Model
**Free Tier**:
- TSX 60 stocks only
- Basic YTD charts
- Limited swipes per day (e.g., 20)

**Premium ($4.99/month)**:
- All TSX stocks (~200+)
- Extended charts (5Y, 10Y)
- Unlimited swipes
- Portfolio tracking
- Price alerts

---

## 📚 Resources & Documentation

### APIs & Services
- [Supabase Docs](https://supabase.com/docs)
- [yfinance Documentation](https://pypi.org/project/yfinance/)
- [React Native Docs](https://reactnative.dev/)
- [Expo Docs](https://docs.expo.dev/)

### Design Inspiration
- Tinder UI/UX patterns
- Robinhood (stock display)
- Wealthsimple (Canadian context)

### TSX Stock Data
- [TMX Money](https://money.tmx.com/) - Official TSX site
- [Yahoo Finance Canada](https://ca.finance.yahoo.com/)

---

## 🚀 Next Immediate Steps (Priority Order)

### This Week
1. **Generate AI summaries** for all 60 stocks
   - Source company descriptions
   - Create `generate_summaries.py` script
   - Populate `ai_summary` column

2. **Initialize React Native app**
   - Set up Expo project
   - Configure Supabase client
   - Build basic navigation structure

3. **Build StockCard component**
   - Design card layout
   - Integrate chart image
   - Display all stock data fields

### Next Week
4. **Implement swipe mechanics**
   - Add gesture handling
   - Card stack animation
   - Queue management

5. **Set up authentication**
   - Supabase Auth integration
   - Login/signup screens
   - Protected routes

6. **Create user tables**
   - `user_swipes` table
   - `user_watchlist` table
   - API functions for CRUD

### Week After
7. **Build watchlist screen**
   - Display saved stocks
   - Remove from watchlist
   - Sort/filter options

8. **Testing & polish**
   - Real device testing
   - Performance optimization
   - Bug fixes

9. **Soft launch prep**
   - TestFlight build (iOS)
   - Beta tester feedback
   - Iterate on UX

---

## 🤔 Open Questions & Decisions Needed

### Data
- [ ] Where to source original company descriptions for AI summaries?
  - Option A: Scrape from TSX website
  - Option B: Use Yahoo Finance profiles
  - Option C: Manual research and input
  - **Decision needed before generating summaries**

### Frontend
- [ ] Which state management library?
  - React Context (simple, built-in)
  - Zustand (lightweight, good DX)
  - Redux Toolkit (overkill for MVP?)

- [ ] Styling approach?
  - NativeWind (Tailwind for RN)
  - styled-components
  - StyleSheet (vanilla RN)

### Features
- [ ] Should users see stocks they've already swiped?
  - Option A: Never show again
  - Option B: Show again after X days
  - Option C: Let user reset their swipes

- [ ] Swipe direction meaning?
  - Right = Interested (add to watchlist)
  - Left = Not interested (skip)
  - Up = Super interested (future feature?)

### Infrastructure
- [ ] Where to deploy backend scripts for automation?
  - GitHub Actions (free, simple)
  - Railway (paid, reliable)
  - Supabase Edge Functions (native, experimental)

---

## 📝 Notes & Learnings

### What Worked Well
- **Supabase** - Incredibly fast to set up and iterate on schema
- **yfinance** - Reliable for TSX data (despite CAR.UN issue)
- **Batch operations** - Upserting 11K records in ~30 seconds
- **Chart automation** - matplotlib makes beautiful charts with minimal code

### What Was Challenging
- **TSX ticker formats** - `.UN` and `.A`/`.B` suffixes are inconsistent in yfinance
- **Rate limiting** - Yahoo Finance occasionally throttles requests (handled with retries)
- **Chart consistency** - Ensuring all 59 charts have same styling/formatting

### Key Insights
- Users want **engagement**, not just data dumps
- Swipe mechanic makes browsing stocks **fun** vs overwhelming
- AI summaries need to be **exciting**, not just factual
- Charts provide **instant visual feedback** on performance

---

## 🎨 Design Principles

1. **Mobile-first** - Optimize for thumb-scrolling
2. **Scannable** - Key info visible without scrolling
3. **Visual hierarchy** - Price and YTD% should pop
4. **Delightful animations** - Smooth swipes, satisfying feedback
5. **Trust-building** - Real data, clear sources, transparent

---

## 📞 Contact & Support

**Developer**: Jorden Shaw  
**Organization**: Inland Technologies Canada Inc  
**Project Type**: Internal MVP / Side Project  
**Timeline**: MVP target - 2-4 weeks from today

---

**Last Updated**: November 7, 2025  
**Version**: 0.1.0 (Pre-MVP)  
**Status**: 🟡 In Active Development
