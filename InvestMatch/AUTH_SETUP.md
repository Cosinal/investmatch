# InvestMatch Authentication System

Complete authentication system with login/signup and persistent sessions.

## Features

✅ **Email/Password Authentication** via Supabase Auth
✅ **Persistent Sessions** - Users stay logged in
✅ **Protected Routes** - Must be authenticated to access app
✅ **Auto-Redirect** - Login redirects to app, logout redirects to login
✅ **Beautiful UI** - Matches InvestMatch dark theme

---

## How It Works

### 1. **AuthContext** (`lib/AuthContext.tsx`)
- Manages authentication state globally
- Provides `useAuth()` hook to access user/session
- Handles sign in, sign up, and sign out
- Persists session to AsyncStorage

### 2. **Login Screen** (`app/(auth)/login.tsx`)
- Clean email/password form
- Toggle between Sign In and Sign Up
- Form validation and error handling
- Loading states

### 3. **Protected Routes** (`app/_layout.tsx`)
- Checks authentication status
- Redirects unauthenticated users to `/login`
- Redirects authenticated users to `/swipe`
- Shows loading screen during auth check

### 4. **Profile Screen** (`app/(tabs)/profile.tsx`)
- Displays user email and ID
- Shows placeholder stats (swipes, watchlist, like rate)
- Sign out button with confirmation

---

## Usage

### Sign Up
1. Open app
2. Tap "Don't have an account? Sign Up"
3. Enter email and password (min 6 characters)
4. Tap "Sign Up"
5. Check email to verify account

### Sign In
1. Open app (shows login screen automatically)
2. Enter email and password
3. Tap "Sign In"
4. Automatically redirected to swipe screen

### Sign Out
1. Go to Profile tab
2. Tap "Sign Out" button
3. Confirm in alert
4. Automatically redirected to login screen

---

## Session Persistence

Sessions are automatically saved to AsyncStorage and persist across app restarts:

```typescript
// On sign in
await AsyncStorage.setItem('supabase.session', JSON.stringify(session));

// On sign out
await AsyncStorage.removeItem('supabase.session');

// On app start
const session = await supabase.auth.getSession();
```

Users stay logged in until they explicitly sign out.

---

## Integration with User Tracking

The `user.id` from authentication is used in the user tracking system:

```typescript
const { user } = useAuth();

// Record swipe
await supabase.from('user_swipes').insert({
  user_id: user.id,  // Authenticated user ID
  company_id: stockId,
  swipe_direction: 'right'
});
```

This ensures:
- ✅ Users can only see their own data (RLS policies)
- ✅ Swipes are tied to the logged-in user
- ✅ Watchlist is user-specific

---

## File Structure

```
InvestMatch/
├── lib/
│   └── AuthContext.tsx          # Auth state management
├── app/
│   ├── _layout.tsx              # Root layout with auth routing
│   ├── (auth)/
│   │   ├── _layout.tsx          # Auth group layout
│   │   └── login.tsx            # Login/Signup screen
│   └── (tabs)/
│       ├── profile.tsx          # Profile with sign out
│       ├── swipe.tsx            # Protected swipe screen
│       └── watchlist.tsx        # Protected watchlist
```

---

## Customization

### Change Login Screen Style
Edit `app/(auth)/login.tsx`:
```typescript
const styles = StyleSheet.create({
  // Customize colors, fonts, spacing
});
```

### Add Social Auth (Google, Apple)
Update `AuthContext.tsx`:
```typescript
const signInWithGoogle = async () => {
  await supabase.auth.signInWithOAuth({ provider: 'google' });
};
```

### Add "Forgot Password"
Add to `login.tsx`:
```typescript
const resetPassword = async (email: string) => {
  await supabase.auth.resetPasswordForEmail(email);
};
```

---

## Testing

### Test Login Flow
1. Start app: `npx expo start --tunnel --clear`
2. Sign up with test email
3. Sign in
4. Verify redirect to swipe screen
5. Go to profile and sign out
6. Verify redirect to login screen

### Test Session Persistence
1. Sign in
2. Close app completely
3. Reopen app
4. Should stay logged in (no login screen)

---

## Troubleshooting

**App stuck on loading screen:**
- Check Supabase connection in `.env`
- Verify `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_ANON_KEY` are set

**Can't sign up:**
- Check Supabase dashboard → Authentication → Email Templates
- Verify email confirmation is enabled or disabled in Settings

**Session not persisting:**
- Check AsyncStorage permissions
- Clear app data and try again

**RLS errors after login:**
- Verify user_swipes and user_watchlist tables have correct RLS policies
- Check that user ID from auth matches database foreign key

---

## Next Steps

- [ ] Add forgot password functionality
- [ ] Add social auth (Google, Apple)
- [ ] Display real stats on profile (from user_swipes)
- [ ] Add profile photo upload
- [ ] Add email verification reminder
- [ ] Add account deletion option
