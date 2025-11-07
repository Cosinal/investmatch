# InvestMatch User Tracking System

Complete system for tracking user swipes and watchlists in the InvestMatch Tinder-style stock discovery app.

## Overview

This system provides:
- **User Swipes Table**: Records every left/right swipe action
- **User Watchlist Table**: Stores stocks users want to monitor
- **Row Level Security (RLS)**: Ensures users only see their own data
- **Helper Functions**: Convenient SQL functions for common queries
- **Testing Scripts**: Verify everything works correctly

---

## Quick Start

### Step 1: Set Up Database Tables

1. Open your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Create a new query
4. Copy and paste the contents of `create_user_tracking_tables.sql`
5. Click **Run** to execute

This creates:
- `user_swipes` table
- `user_watchlist` table
- RLS policies
- Helper SQL functions

### Step 2: Verify Setup

Run this query in Supabase SQL Editor to verify tables were created:

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('user_swipes', 'user_watchlist');

-- Check RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE tablename IN ('user_swipes', 'user_watchlist');
```

Expected output:
```
user_swipes      | true
user_watchlist   | true
```

### Step 3: Test the System

Run the Python test script:

```bash
python test_user_tracking.py
```

This will:
- Simulate swiping on 10 random stocks (5 left, 5 right)
- Add right-swiped stocks to watchlist
- Display swipe history and watchlist
- Show statistics

---

## Database Schema

### user_swipes Table

Tracks every swipe action (permanent record).

```sql
id               BIGSERIAL PRIMARY KEY
user_id          UUID (FK to auth.users)
company_id       BIGINT (FK to stocks)
swipe_direction  TEXT ('left' or 'right')
swiped_at        TIMESTAMP
```

**Constraints:**
- Unique on (user_id, company_id) - prevents duplicate swipes
- Check constraint: swipe_direction IN ('left', 'right')

**RLS Policies:**
- Users can SELECT their own swipes
- Users can INSERT their own swipes
- No UPDATE or DELETE (swipes are permanent)

### user_watchlist Table

Stores stocks users are actively monitoring.

```sql
id          BIGSERIAL PRIMARY KEY
user_id     UUID (FK to auth.users)
company_id  BIGINT (FK to stocks)
added_at    TIMESTAMP
notes       TEXT (optional)
```

**Constraints:**
- Unique on (user_id, company_id) - prevents duplicates

**RLS Policies:**
- Users can SELECT their own watchlist
- Users can INSERT into their own watchlist
- Users can UPDATE their own watchlist (edit notes)
- Users can DELETE from their own watchlist

---

## Helper SQL Functions

### get_user_swipe_stats(user_uuid)

Returns swipe statistics for a user.

```sql
SELECT * FROM get_user_swipe_stats('your-user-uuid-here');
```

Returns:
```
total_swipes  | left_swipes | right_swipes | swipe_rate
10            | 5           | 5            | 50.00
```

### get_unswiped_stocks(user_uuid)

Returns stocks the user hasn't swiped on yet.

```sql
SELECT * FROM get_unswiped_stocks('your-user-uuid-here') LIMIT 10;
```

Returns list of stocks ordered by market cap.

### add_to_watchlist_from_swipe(user_uuid, company_id)

Adds a stock to watchlist (typically called after right swipe).

```sql
SELECT add_to_watchlist_from_swipe('user-uuid', 123);
```

Returns `true` if successful.

### remove_from_watchlist(user_uuid, company_id)

Removes a stock from watchlist.

```sql
SELECT remove_from_watchlist('user-uuid', 123);
```

Returns `true` if item was removed.

---

## Integration with React Native App

### Recording Swipes

Update [swipe.tsx](InvestMatch/app/(tabs)/swipe.tsx) to record swipes:

```typescript
// In onSwipedRight handler
onSwipedRight={async (index) => {
  const stock = stocks[index];

  // Record the swipe
  await supabase.from('user_swipes').insert({
    user_id: userId, // from useUserId hook
    company_id: stock.id,
    swipe_direction: 'right'
  });

  // Add to watchlist
  await supabase.from('user_watchlist').insert({
    user_id: userId,
    company_id: stock.id
  });
}}

onSwipedLeft={async (index) => {
  const stock = stocks[index];

  // Record the swipe
  await supabase.from('user_swipes').insert({
    user_id: userId,
    company_id: stock.id,
    swipe_direction: 'left'
  });
}}
```

### Loading Watchlist

Update [watchlist.tsx](InvestMatch/app/(tabs)/watchlist.tsx) to display user's watchlist:

```typescript
const { data: watchlist } = await supabase
  .from('user_watchlist')
  .select(`
    *,
    stocks (
      id,
      ticker,
      name,
      current_price,
      ytd_return,
      chart_image_url
    )
  `)
  .order('added_at', { ascending: false });
```

### Filtering Already-Swiped Stocks

Update swipe query to exclude already-swiped stocks:

```typescript
// Get stocks user hasn't swiped on
const { data: unswipedStocks } = await supabase
  .rpc('get_unswiped_stocks', { user_uuid: userId })
  .limit(60);
```

---

## Testing Checklist

After running `create_user_tracking_tables.sql`:

- [ ] Tables created successfully
  ```sql
  SELECT * FROM user_swipes LIMIT 1;
  SELECT * FROM user_watchlist LIMIT 1;
  ```

- [ ] RLS enabled on both tables
  ```sql
  SELECT tablename, rowsecurity FROM pg_tables
  WHERE tablename IN ('user_swipes', 'user_watchlist');
  ```

- [ ] Helper functions exist
  ```sql
  SELECT routine_name FROM information_schema.routines
  WHERE routine_name LIKE 'get_%' OR routine_name LIKE '%watchlist%';
  ```

- [ ] Can insert swipes
  ```sql
  INSERT INTO user_swipes (user_id, company_id, swipe_direction)
  VALUES (auth.uid(), 1, 'right');
  ```

- [ ] Can query own data
  ```sql
  SELECT * FROM user_swipes WHERE user_id = auth.uid();
  ```

- [ ] Python test script runs successfully
  ```bash
  python test_user_tracking.py
  ```

---

## Common Queries

### Get user's swipe history with stock details

```sql
SELECT
  us.*,
  s.ticker,
  s.name,
  s.current_price
FROM user_swipes us
JOIN stocks s ON us.company_id = s.id
WHERE us.user_id = auth.uid()
ORDER BY us.swiped_at DESC;
```

### Get user's watchlist with performance data

```sql
SELECT
  uw.*,
  s.ticker,
  s.name,
  s.current_price,
  s.ytd_return,
  s.chart_image_url
FROM user_watchlist uw
JOIN stocks s ON uw.company_id = s.id
WHERE uw.user_id = auth.uid()
ORDER BY uw.added_at DESC;
```

### Get stocks user liked but hasn't added to watchlist

```sql
SELECT
  us.company_id,
  s.ticker,
  s.name
FROM user_swipes us
JOIN stocks s ON us.company_id = s.id
LEFT JOIN user_watchlist uw ON us.company_id = uw.company_id AND us.user_id = uw.user_id
WHERE us.user_id = auth.uid()
  AND us.swipe_direction = 'right'
  AND uw.id IS NULL;
```

---

## Security Notes

**Row Level Security (RLS):**
- All queries are automatically filtered by `auth.uid()`
- Users CANNOT see other users' swipes or watchlists
- Service role key bypasses RLS (use carefully in admin tools only)

**Anonymous Users:**
- If using anonymous auth, make sure to link sessions properly
- Consider prompting users to create accounts to save their data permanently

**Data Privacy:**
- User swipes are private and permanent
- No other user can see what stocks you've swiped on
- Watchlist data is user-specific

---

## Troubleshooting

**Error: "relation user_swipes does not exist"**
- Run `create_user_tracking_tables.sql` in Supabase SQL Editor

**Error: "new row violates row-level security policy"**
- Make sure you're using authenticated user ID
- Check that RLS policies are correctly defined

**Error: "duplicate key value violates unique constraint"**
- User already swiped on this stock (this is expected behavior)
- Use `ON CONFLICT DO NOTHING` in your INSERT queries

**Function not found errors:**
- Verify helper functions were created:
  ```sql
  SELECT routine_name FROM information_schema.routines;
  ```

**Test script fails:**
- Verify `.env` has correct Supabase credentials
- Make sure `stocks` table has data
- Check Supabase dashboard for error logs

---

## Next Steps

1. ✅ Run `create_user_tracking_tables.sql` in Supabase
2. ✅ Run `python test_user_tracking.py` to verify
3. 🔄 Integrate swipe tracking in React Native app
4. 🔄 Build watchlist UI
5. 📊 Add analytics dashboard for user engagement
6. 🔔 Add push notifications for watchlist stock alerts

---

## Files

- `create_user_tracking_tables.sql` - Complete schema with RLS and functions
- `test_user_tracking.py` - Python testing script
- `USER_TRACKING_README.md` - This documentation
