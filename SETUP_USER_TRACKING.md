# Quick Setup Guide - User Tracking System

## 📋 Overview

This system tracks user swipes and watchlists in InvestMatch.

**What it does:**
- Records every swipe (left = pass, right = like)
- Maintains user watchlists for stocks they're interested in
- Enforces data privacy with Row Level Security
- Provides helper functions for common queries

---

## 🚀 Setup (5 minutes)

### Step 1: Run SQL in Supabase (2 min)

1. Open [Supabase Dashboard](https://app.supabase.com)
2. Go to **SQL Editor** → **New Query**
3. Copy/paste contents of `create_user_tracking_tables.sql`
4. Click **Run**

✅ Creates 2 tables, RLS policies, and 4 helper functions

### Step 2: Verify (1 min)

Run this in SQL Editor:

```sql
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('user_swipes', 'user_watchlist');
```

Expected output: 2 rows

### Step 3: Test (2 min)

```bash
python test_user_tracking.py
```

✅ Should show swipe simulation and watchlist creation

---

## 📊 What Was Created

### Tables

**user_swipes**
- Tracks every left/right swipe
- Swipes are permanent (no edits/deletes)
- Unique constraint prevents duplicate swipes

**user_watchlist**
- Stores stocks user wants to monitor
- Users can add/edit/remove watchlist items
- Supports optional notes

### Security

**Row Level Security (RLS) Enabled**
- Users can ONLY see their own data
- Automatic filtering by `auth.uid()`
- Service role bypasses RLS (admin only)

### Functions

**get_user_swipe_stats(uuid)** - Returns swipe statistics
**get_unswiped_stocks(uuid)** - Returns stocks not yet swiped
**add_to_watchlist_from_swipe(uuid, id)** - Adds to watchlist
**remove_from_watchlist(uuid, id)** - Removes from watchlist

---

## 🔌 React Native Integration

### Record Swipes

In `swipe.tsx`:

```typescript
onSwipedRight={async (index) => {
  const stock = stocks[index];
  const userId = await getUserId(); // from useUserId hook

  // Record swipe
  await supabase.from('user_swipes').insert({
    user_id: userId,
    company_id: stock.id,
    swipe_direction: 'right'
  });

  // Add to watchlist
  await supabase.from('user_watchlist').insert({
    user_id: userId,
    company_id: stock.id
  });
}}
```

### Load Watchlist

In `watchlist.tsx`:

```typescript
const { data: watchlist } = await supabase
  .from('user_watchlist')
  .select(`
    *,
    stocks (ticker, name, current_price, ytd_return, chart_image_url)
  `)
  .eq('user_id', userId)
  .order('added_at', { ascending: false });
```

### Filter Unswiped Stocks

In `swipe.tsx`:

```typescript
const { data: stocks } = await supabase
  .rpc('get_unswiped_stocks', { user_uuid: userId })
  .limit(60);
```

---

## ✅ Testing Checklist

After setup, verify:

- [ ] `user_swipes` table exists
- [ ] `user_watchlist` table exists
- [ ] RLS is enabled on both tables
- [ ] Helper functions work (run test script)
- [ ] Can insert swipes via Supabase client
- [ ] Can query user's own data
- [ ] Cannot see other users' data

---

## 🔧 Troubleshooting

**Table doesn't exist:**
→ Run `create_user_tracking_tables.sql` in Supabase SQL Editor

**RLS policy error:**
→ Make sure using authenticated user ID (`auth.uid()`)

**Duplicate swipe error:**
→ Expected - use `ON CONFLICT DO NOTHING` in INSERT

**Test script fails:**
→ Check `.env` has correct Supabase URL and Service Role Key

---

## 📚 Full Documentation

See [USER_TRACKING_README.md](USER_TRACKING_README.md) for:
- Complete schema details
- All SQL functions
- Integration examples
- Security notes
- Common queries

---

## 🎯 Next Steps

1. ✅ Complete setup above
2. 🔄 Integrate into React Native app
3. 🔄 Build watchlist UI
4. 📊 Add user analytics
5. 🔔 Push notifications for watchlist alerts
