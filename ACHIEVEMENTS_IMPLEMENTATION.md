# Achievement System - Backend Implementation

This document describes the achievement system implementation for the UTrack workout tracking application. This serves as a reference for the frontend implementation.

## Table of Contents
1. [Overview](#overview)
2. [Data Models](#data-models)
3. [API Endpoints](#api-endpoints)
4. [Achievement Categories](#achievement-categories)
5. [Automatic Tracking](#automatic-tracking)
6. [Statistics & Percentiles](#statistics--percentiles)
7. [Frontend Integration Guide](#frontend-integration-guide)

---

## Overview

The achievement system provides:
- **Workout Count Achievements**: Earn badges for completing X workouts
- **Streak Achievements**: Earn badges for consecutive workout days
- **PR (Personal Record) Achievements**: Earn badges for lifting specific weights on exercises (e.g., "Bench Press 100kg")
- **Volume Achievements**: Earn badges for total lifetime volume lifted
- **User Statistics**: Track total workouts, volume, streaks, PRs, and points
- **Exercise Rankings/Percentiles**: Show users where they rank (e.g., "Top 5% of bench pressers")
- **Leaderboards**: Compare with other users on specific exercises

---

## Data Models

### Achievement
Master achievement definitions stored in the database.

```typescript
interface Achievement {
  id: string;                    // UUID
  name: string;                  // e.g., "Century Club"
  description: string;           // e.g., "Complete 100 workouts"
  icon: string;                  // Icon identifier for frontend (e.g., "workout_100")
  category: AchievementCategory;
  category_display: string;      // Human-readable category name
  rarity: AchievementRarity;
  rarity_display: string;        // Human-readable rarity name
  requirement_value: number;     // Value needed to earn (e.g., 100 for 100 workouts)
  exercise: string | null;       // Exercise UUID (for PR achievements)
  exercise_name: string | null;  // Exercise name (for PR achievements)
  muscle_group: string | null;   // For muscle-based achievements
  points: number;                // XP points awarded
  is_hidden: boolean;            // Hidden achievements revealed when earned
  order: number;                 // Display order within category
}

type AchievementCategory =
  | 'workout_count'      // Complete X workouts
  | 'workout_streak'     // X consecutive days
  | 'pr_weight'          // Lift X kg on specific exercise
  | 'pr_one_rep_max'     // Achieve X kg estimated 1RM
  | 'total_volume'       // Lift X kg total lifetime
  | 'exercise_count'     // Do X different exercises
  | 'muscle_volume'      // X sets on specific muscle
  | 'consistency';       // X workouts per week/month

type AchievementRarity =
  | 'common'      // Easy to achieve
  | 'uncommon'    // Moderate effort
  | 'rare'        // Significant effort
  | 'epic'        // Major milestone
  | 'legendary'; // Elite achievement
```

### UserAchievement
Tracks which achievements a user has earned.

```typescript
interface UserAchievement {
  id: string;
  achievement: Achievement;
  earned_at: string;           // ISO datetime when earned
  current_progress: number;    // Current value achieved
  earned_value: number | null; // Actual value when earned (for PRs)
  is_notified: boolean;        // Has user seen the notification?
  progress_percentage: number; // 0-100
}
```

### PersonalRecord
Tracks user's best performances per exercise.

```typescript
interface PersonalRecord {
  id: string;
  exercise: Exercise;
  exercise_id: string;

  // Best weight lifted
  best_weight: number;
  best_weight_reps: number;
  best_weight_date: string | null;

  // Best estimated 1RM (Brzycki formula)
  best_one_rep_max: number;
  best_one_rep_max_weight: number;
  best_one_rep_max_reps: number;
  best_one_rep_max_date: string | null;

  // Best set volume (weight × reps)
  best_set_volume: number;
  best_set_volume_date: string | null;

  // Lifetime totals
  total_volume: number;
  total_sets: number;
  total_reps: number;

  created_at: string;
  updated_at: string;
}
```

### UserStatistics
Aggregated user statistics.

```typescript
interface UserStatistics {
  id: string;

  // Workout stats
  total_workouts: number;
  total_workout_duration: number;  // seconds

  // Volume stats
  total_volume: number;            // kg
  total_sets: number;
  total_reps: number;

  // Streak stats
  current_streak: number;          // days
  longest_streak: number;          // days
  last_workout_date: string | null;

  // Achievement stats
  total_achievements: number;
  total_points: number;

  // PR stats
  total_prs: number;
  prs_this_month: number;

  created_at: string;
  updated_at: string;
}
```

---

## API Endpoints

Base URL: `/api/achievements/`

### Achievement Endpoints

#### GET `/list/`
Get all achievements with user's progress.

**Query Parameters:**
- `category` (optional): Filter by category

**Response:**
```json
[
  {
    "achievement": { /* Achievement object */ },
    "is_earned": true,
    "current_progress": 150,
    "progress_percentage": 100,
    "earned_at": "2024-01-15T10:30:00Z",
    "earned_value": 150
  }
]
```

#### GET `/earned/`
Get only user's earned achievements.

**Response:** Array of `UserAchievement` objects

#### GET `/categories/`
Get achievement categories with completion stats.

**Response:**
```json
[
  {
    "code": "workout_count",
    "name": "Workout Count",
    "total": 9,
    "earned": 3,
    "progress_percentage": 33.3
  }
]
```

#### GET `/unnotified/`
Get achievements earned but not yet shown to user.

**Response:**
```json
[
  {
    "achievement": { /* Achievement object */ },
    "earned_at": "2024-01-15T10:30:00Z",
    "earned_value": 100,
    "message": "Achievement unlocked: Century Club!"
  }
]
```

#### POST `/unnotified/mark-seen/`
Mark achievements as seen/notified.

**Request Body:**
```json
{
  "achievement_ids": ["uuid1", "uuid2"]  // Optional - marks all if empty
}
```

### Personal Record Endpoints

#### GET `/prs/`
Get all user's personal records (summary).

**Response:**
```json
[
  {
    "id": "uuid",
    "exercise_id": "uuid",
    "exercise_name": "Bench Press",
    "best_weight": 100,
    "best_one_rep_max": 115.5,
    "total_volume": 50000
  }
]
```

#### GET `/prs/<exercise_id>/`
Get detailed PR for specific exercise.

**Response:** Full `PersonalRecord` object with nested `Exercise`

### Statistics Endpoints

#### GET `/stats/`
Get user's overall statistics.

**Response:** `UserStatistics` object

#### POST `/recalculate/`
Force recalculate all statistics and check for new achievements.
Useful after data import or to fix discrepancies.

**Response:**
```json
{
  "status": "ok",
  "new_achievements": 3,
  "stats": { /* UserStatistics object */ }
}
```

### Ranking & Percentile Endpoints

#### GET `/ranking/<exercise_id>/`
Get user's ranking/percentile for a specific exercise.

**Response:**
```json
{
  "exercise_id": "uuid",
  "exercise_name": "Bench Press",
  "user_best_weight": 100,
  "user_best_one_rm": 115.5,
  "weight_percentile": 85,
  "one_rm_percentile": 90,
  "total_users": 1250,
  "percentile_message": "Top 10%! Only 10% of users can lift this much on Bench Press."
}
```

#### GET `/rankings/`
Get user's ranking for all exercises they have PRs in.

**Response:** Array of ranking objects (sorted by percentile, best first)

#### GET `/leaderboard/<exercise_id>/`
Get leaderboard for a specific exercise.

**Query Parameters:**
- `limit` (default: 10): Number of entries
- `stat` (default: 'one_rm'): 'weight' or 'one_rm'

**Response:**
```json
{
  "exercise_id": "uuid",
  "exercise_name": "Bench Press",
  "stat_type": "one_rm",
  "leaderboard": [
    {
      "rank": 1,
      "user_id": "uuid",
      "display_name": "John",
      "value": 180.5,
      "is_current_user": false
    }
  ],
  "user_entry": {  // Only if user not in top list
    "rank": 45,
    "user_id": "uuid",
    "display_name": "You",
    "value": 115.5,
    "is_current_user": true
  }
}
```

---

## Achievement Categories

### Workout Count (9 achievements)
| Name | Requirement | Rarity | Points |
|------|-------------|--------|--------|
| First Steps | 1 workout | Common | 10 |
| Getting Started | 5 workouts | Common | 25 |
| Committed | 10 workouts | Common | 50 |
| Dedicated | 25 workouts | Uncommon | 100 |
| Gym Regular | 50 workouts | Uncommon | 200 |
| Century Club | 100 workouts | Rare | 500 |
| Iron Dedication | 250 workouts | Epic | 1000 |
| Legendary Lifter | 500 workouts | Legendary | 2500 |
| Iron Legend | 1000 workouts | Legendary | 5000 |

### Workout Streak (7 achievements)
| Name | Requirement | Rarity | Points |
|------|-------------|--------|--------|
| Warm Up | 2 days | Common | 15 |
| Hat Trick | 3 days | Common | 25 |
| Week Warrior | 7 days | Uncommon | 100 |
| Two Week Titan | 14 days | Rare | 250 |
| Monthly Monster | 30 days | Epic | 750 |
| Unstoppable | 60 days | Legendary | 2000 |
| Machine | 100 days | Legendary | 5000 |

### Total Volume (7 achievements)
| Name | Requirement | Rarity | Points |
|------|-------------|--------|--------|
| First Ton | 1,000 kg | Common | 15 |
| Heavy Lifter | 10,000 kg | Common | 50 |
| Volume Veteran | 50,000 kg | Uncommon | 150 |
| 100K Club | 100,000 kg | Rare | 350 |
| Quarter Million | 250,000 kg | Epic | 750 |
| Half Million | 500,000 kg | Epic | 1500 |
| Million Pound Club | 1,000,000 kg | Legendary | 5000 |

### PR Achievements (Dynamic)
PR achievements are created for major exercises with milestones:

**Bench Press**: 40, 60, 80, 100, 120, 140, 160, 180, 200, 225 kg
**Squat**: 60, 80, 100, 120, 140, 160, 180, 200, 225, 250 kg
**Deadlift**: 60, 100, 120, 140, 160, 180, 200, 225, 250, 300 kg
**Overhead Press**: 30, 40, 50, 60, 70, 80, 90, 100, 110, 120 kg
**And more...**

Rarity scales with difficulty:
- Lower weights: Common → Uncommon
- Mid weights: Rare
- High weights: Epic → Legendary

---

## Automatic Tracking

The system automatically tracks achievements through Django signals:

### When a Set is Added
1. PR is checked and updated if the set beats existing records
2. Weight PR, 1RM PR, and Volume PR are checked independently
3. If new PR: relevant PR achievements are checked and awarded

### When a Workout is Completed
1. User statistics are updated (workout count, duration, streak)
2. Workout count achievements are checked
3. Streak achievements are checked

### Signal Flow
```
ExerciseSet.post_save → track_set_for_pr() → update_personal_record() → check_achievements_for_pr()
Workout.post_save (is_done=True) → check_workout_achievements()
User.post_save (created=True) → create_user_statistics()
```

---

## Statistics & Percentiles

### Percentile Calculation
Percentiles are calculated using all users' PRs for an exercise:

```python
# Percentiles stored: 10, 25, 50 (median), 75, 90, 95, 99
# User percentile = where their value falls in distribution
```

### Percentile Messages
Based on user's percentile, messages are generated:
- **≥90%**: "Top {X}%! Only {X}% of users can lift this much on {exercise}."
- **75-89%**: "Stronger than {X}% of users on {exercise}!"
- **<75%**: "You're in the top {X}% for {exercise}. Keep pushing!"

### Statistics Refresh
- Exercise statistics are calculated on-demand when accessed
- Can be force-refreshed via `/recalculate/` endpoint
- Stored in `ExerciseStatistics` model for caching

---

## Frontend Integration Guide

### 1. Achievement Display Screen

**Recommended UI Components:**
- Category tabs/pills to filter achievements
- Progress bars for unearned achievements
- Rarity badges (color-coded: Common=gray, Uncommon=green, Rare=blue, Epic=purple, Legendary=gold)
- Lock icon for unearned achievements
- Earned date for completed achievements

**API Calls:**
```typescript
// Load all achievements with progress
GET /api/achievements/list/

// Load categories for tabs
GET /api/achievements/categories/
```

### 2. Achievement Notifications

**Show notification popup when new achievement earned:**
```typescript
// Check for unnotified achievements (on app start, after workout)
GET /api/achievements/unnotified/

// After user dismisses notification
POST /api/achievements/unnotified/mark-seen/
{ "achievement_ids": ["uuid"] }
```

**Notification UI:**
- Celebratory animation/confetti
- Achievement icon, name, description
- Points earned
- Rarity badge

### 3. Personal Records Screen

**Show PRs per exercise:**
```typescript
// Get all PRs
GET /api/achievements/prs/

// Get detailed PR for exercise
GET /api/achievements/prs/{exercise_id}/
```

**PR Card UI:**
- Exercise name and image
- Best weight with reps (e.g., "100kg × 5")
- Estimated 1RM
- Date achieved
- Related PR achievements progress

### 4. User Profile/Stats Screen

**Display overall statistics:**
```typescript
GET /api/achievements/stats/
```

**Stats Dashboard:**
- Total workouts counter
- Current streak (with flame icon)
- Longest streak record
- Total volume lifted
- Achievement count and total points
- PR count

### 5. Exercise Ranking/Comparison

**Show ranking on exercise detail page:**
```typescript
GET /api/achievements/ranking/{exercise_id}/
```

**Ranking UI:**
- Percentile badge (e.g., "Top 10%")
- User's best weight and 1RM
- Total users comparison
- Percentile message

### 6. Leaderboards

**Optional competitive feature:**
```typescript
GET /api/achievements/leaderboard/{exercise_id}/?limit=10&stat=one_rm
```

**Leaderboard UI:**
- Top 10 list with ranks
- Highlight current user if in list
- Show user's rank separately if not in top 10
- Toggle between weight and 1RM

### 7. Real-time Updates

After completing a set:
```typescript
// The backend automatically:
// 1. Updates PR if applicable
// 2. Checks for new achievements
// 3. Updates user statistics

// Frontend should:
// 1. Poll /unnotified/ after workout completion
// 2. Show achievement popup if new achievements
// 3. Update stats display
```

### 8. Data Sync/Import

After importing data:
```typescript
// Force recalculate all stats and achievements
POST /api/achievements/recalculate/
```

---

## Icon Mapping

Achievement icons use identifiers that should map to frontend assets:

| Icon ID Pattern | Suggested Icon |
|-----------------|----------------|
| `first_workout` | Trophy/Star |
| `workout_X` | Dumbbell with number |
| `streak_X` | Fire/Flame with number |
| `volume_Xk` | Weight plates |
| `pr_exercise_weight` | Medal/Crown |

Rarity colors:
- Common: `#9CA3AF` (Gray)
- Uncommon: `#22C55E` (Green)
- Rare: `#3B82F6` (Blue)
- Epic: `#8B5CF6` (Purple)
- Legendary: `#F59E0B` (Gold)

---

## Management Commands

```bash
# Seed initial achievements
python manage.py seed_achievements

# This creates:
# - Workout count achievements (9)
# - Streak achievements (7)
# - Volume achievements (7)
# - PR achievements for existing exercises (varies)
```

---

## File Structure

```
achievements/
├── __init__.py
├── admin.py           # Django admin configuration
├── apps.py            # App configuration with signal loading
├── models.py          # Achievement, UserAchievement, PersonalRecord, etc.
├── serializers.py     # DRF serializers
├── signals.py         # Auto-tracking signals
├── urls.py            # API URL routes
├── views.py           # API views and helper functions
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── seed_achievements.py  # Seed command
└── migrations/
    └── 0001_initial.py
```

---

## Authentication

All endpoints require authentication via JWT token:

```
Authorization: Bearer <access_token>
```

---

## Error Responses

Standard error format:
```json
{
  "error": "Error message description"
}
```

Common status codes:
- `401`: Unauthorized (missing/invalid token)
- `404`: Resource not found (exercise, PR not found)
- `400`: Bad request (invalid parameters)

---

## Notes for Frontend Team

1. **Achievement tracking is automatic** - No need to manually call APIs when sets are added or workouts completed. Just poll `/unnotified/` after workout completion.

2. **Percentiles require sufficient data** - Percentile calculations need multiple users with PRs for meaningful results. Show fallback message when data is insufficient.

3. **Icons are identifiers** - Map icon strings to actual image assets or icon components in the frontend.

4. **Progress is real-time** - The `current_progress` field reflects live data, not cached values.

5. **Rarity affects display** - Use rarity to determine visual treatment (colors, animations, prominence).

6. **Points are gamification** - Total points can be displayed as "XP" or level system if desired.
