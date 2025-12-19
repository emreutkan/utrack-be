# Muscle Recovery API - Frontend Implementation Guide

## Endpoint

```
GET /api/workout/recovery/status/
```

**Authentication:** Required (Bearer token)

**Method:** GET

**Query Parameters:** None

---

## Response Structure

### Success Response (200 OK)

```json
{
  "recovery_status": {
    "chest": {
      "id": 1,
      "muscle_group": "chest",
      "fatigue_score": 4.5,
      "total_sets": 12,
      "recovery_hours": 48,
      "recovery_until": "2024-01-17T10:00:00Z",
      "is_recovered": false,
      "hours_until_recovery": 12.5,
      "recovery_percentage": 75.0,
      "source_workout": 123,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    },
    "shoulders": {
      "id": 2,
      "muscle_group": "shoulders",
      "fatigue_score": 2.1,
      "total_sets": 8,
      "recovery_hours": 36,
      "recovery_until": "2024-01-16T22:00:00Z",
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": 123,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    },
    "biceps": {
      "muscle_group": "biceps",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    },
    "triceps": {
      "muscle_group": "triceps",
      "fatigue_score": 1.8,
      "total_sets": 6,
      "recovery_hours": 30,
      "recovery_until": "2024-01-16T16:00:00Z",
      "is_recovered": false,
      "hours_until_recovery": 6.0,
      "recovery_percentage": 80.0,
      "source_workout": 123,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    },
    "forearms": {
      "muscle_group": "forearms",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    },
    "lats": {
      "id": 3,
      "muscle_group": "lats",
      "fatigue_score": 5.2,
      "total_sets": 15,
      "recovery_hours": 60,
      "recovery_until": "2024-01-18T10:00:00Z",
      "is_recovered": false,
      "hours_until_recovery": 36.0,
      "recovery_percentage": 40.0,
      "source_workout": 123,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    },
    "traps": {
      "muscle_group": "traps",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    },
    "lower_back": {
      "muscle_group": "lower_back",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    },
    "quads": {
      "muscle_group": "quads",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    },
    "hamstrings": {
      "muscle_group": "hamstrings",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    },
    "glutes": {
      "muscle_group": "glutes",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    },
    "calves": {
      "muscle_group": "calves",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    },
    "abs": {
      "muscle_group": "abs",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    },
    "obliques": {
      "muscle_group": "obliques",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    },
    "abductors": {
      "muscle_group": "abductors",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    },
    "adductors": {
      "muscle_group": "adductors",
      "fatigue_score": 0.0,
      "total_sets": 0,
      "recovery_hours": 0,
      "recovery_until": null,
      "is_recovered": true,
      "hours_until_recovery": 0,
      "recovery_percentage": 100,
      "source_workout": null
    }
  },
  "timestamp": "2024-01-16T22:00:00Z"
}
```

---

## Field Descriptions

### Recovery Status Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | number \| null | Recovery record ID (null if no recovery data exists) |
| `muscle_group` | string | Muscle group identifier (chest, biceps, quads, etc.) |
| `fatigue_score` | number | Total fatigue accumulated from sets (higher = more fatigue) |
| `total_sets` | number | Total number of sets performed for this muscle |
| `recovery_hours` | number | Total hours needed for full recovery |
| `recovery_until` | string \| null | ISO 8601 timestamp when recovery completes (null if recovered or no data) |
| `is_recovered` | boolean | `true` if muscle is fully recovered, `false` if still recovering |
| `hours_until_recovery` | number | Hours remaining until full recovery (0 if recovered) |
| `recovery_percentage` | number | Recovery progress 0-100 (100 = fully recovered) |
| `source_workout` | number \| null | ID of workout that caused this fatigue (null if no data) |
| `created_at` | string \| null | ISO 8601 timestamp when recovery record was created |
| `updated_at` | string \| null | ISO 8601 timestamp when recovery record was last updated |

### Root Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `recovery_status` | object | Dictionary mapping muscle_group → recovery data |
| `timestamp` | string | ISO 8601 timestamp of when the response was generated |

---

## Muscle Group Identifiers

All possible muscle group values:

- `chest`
- `shoulders`
- `biceps`
- `triceps`
- `forearms`
- `lats`
- `traps`
- `lower_back`
- `quads`
- `hamstrings`
- `glutes`
- `calves`
- `abs`
- `obliques`
- `abductors`
- `adductors`

---

## TypeScript Interface

```typescript
interface MuscleRecovery {
  id: number | null;
  muscle_group: string;
  fatigue_score: number;
  total_sets: number;
  recovery_hours: number;
  recovery_until: string | null;
  is_recovered: boolean;
  hours_until_recovery: number;
  recovery_percentage: number;
  source_workout: number | null;
  created_at: string | null;
  updated_at: string | null;
}

interface RecoveryStatusResponse {
  recovery_status: Record<string, MuscleRecovery>;
  timestamp: string;
}
```

---

## API Service Example

```typescript
// services/recoveryService.ts
import axios from 'axios';

const API_BASE_URL = 'http://your-api-url/api/workout';

export interface MuscleRecovery {
  id: number | null;
  muscle_group: string;
  fatigue_score: number;
  total_sets: number;
  recovery_hours: number;
  recovery_until: string | null;
  is_recovered: boolean;
  hours_until_recovery: number;
  recovery_percentage: number;
  source_workout: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface RecoveryStatusResponse {
  recovery_status: Record<string, MuscleRecovery>;
  timestamp: string;
}

export const getRecoveryStatus = async (
  token: string
): Promise<RecoveryStatusResponse> => {
  const response = await axios.get(
    `${API_BASE_URL}/recovery/status/`,
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  return response.data;
};
```

---

## React Hook Example

```typescript
// hooks/useMuscleRecovery.ts
import { useState, useEffect } from 'react';
import { getRecoveryStatus, MuscleRecovery, RecoveryStatusResponse } from '../services/recoveryService';

export const useMuscleRecovery = (token?: string) => {
  const [recoveryStatus, setRecoveryStatus] = useState<Record<string, MuscleRecovery>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timestamp, setTimestamp] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    const fetchRecovery = async () => {
      try {
        setLoading(true);
        const data = await getRecoveryStatus(token);
        setRecoveryStatus(data.recovery_status);
        setTimestamp(data.timestamp);
        setError(null);
      } catch (err) {
        setError('Failed to load recovery status');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecovery();
  }, [token]);

  return { recoveryStatus, loading, error, timestamp };
};
```

---

## Data Processing Examples

### Get All Recovering Muscles

```typescript
const recoveringMuscles = Object.entries(recoveryStatus)
  .filter(([_, status]) => !status.is_recovered)
  .map(([muscle, status]) => ({
    muscle,
    hoursRemaining: status.hours_until_recovery,
    percentage: status.recovery_percentage
  }));
```

### Get Fully Recovered Muscles

```typescript
const recoveredMuscles = Object.entries(recoveryStatus)
  .filter(([_, status]) => status.is_recovered)
  .map(([muscle]) => muscle);
```

### Get Muscles by Recovery Percentage Range

```typescript
const getMusclesByRecoveryRange = (
  recoveryStatus: Record<string, MuscleRecovery>,
  min: number,
  max: number
) => {
  return Object.entries(recoveryStatus)
    .filter(([_, status]) => 
      status.recovery_percentage >= min && 
      status.recovery_percentage <= max
    )
    .map(([muscle, status]) => ({
      muscle,
      percentage: status.recovery_percentage,
      hoursRemaining: status.hours_until_recovery
    }));
};

// Example: Get muscles 50-75% recovered
const partiallyRecovered = getMusclesByRecoveryRange(recoveryStatus, 50, 75);
```

### Sort Muscles by Recovery Time

```typescript
const sortedByRecoveryTime = Object.entries(recoveryStatus)
  .filter(([_, status]) => !status.is_recovered)
  .sort(([_, a], [__, b]) => 
    a.hours_until_recovery - b.hours_until_recovery
  )
  .map(([muscle, status]) => ({
    muscle,
    hoursRemaining: status.hours_until_recovery,
    percentage: status.recovery_percentage
  }));
```

### Get Muscles Ready for Training

```typescript
const readyForTraining = Object.entries(recoveryStatus)
  .filter(([_, status]) => status.is_recovered || status.recovery_percentage >= 90)
  .map(([muscle]) => muscle);
```

### Calculate Average Recovery Percentage

```typescript
const calculateAverageRecovery = (
  recoveryStatus: Record<string, MuscleRecovery>
): number => {
  const percentages = Object.values(recoveryStatus)
    .map(status => status.recovery_percentage);
  
  if (percentages.length === 0) return 100;
  
  const sum = percentages.reduce((acc, val) => acc + val, 0);
  return sum / percentages.length;
};
```

### Get Most Fatigued Muscles

```typescript
const mostFatigued = Object.entries(recoveryStatus)
  .filter(([_, status]) => status.fatigue_score > 0)
  .sort(([_, a], [__, b]) => b.fatigue_score - a.fatigue_score)
  .slice(0, 5)
  .map(([muscle, status]) => ({
    muscle,
    fatigueScore: status.fatigue_score,
    sets: status.total_sets
  }));
```

### Check if Specific Muscle is Recovered

```typescript
const isMuscleRecovered = (
  recoveryStatus: Record<string, MuscleRecovery>,
  muscleGroup: string
): boolean => {
  const status = recoveryStatus[muscleGroup];
  return status ? status.is_recovered : true; // Default to recovered if no data
};
```

### Get Recovery Timeline

```typescript
const getRecoveryTimeline = (
  recoveryStatus: Record<string, MuscleRecovery>
): Array<{ muscle: string; recoveryTime: Date; hoursRemaining: number }> => {
  return Object.entries(recoveryStatus)
    .filter(([_, status]) => status.recovery_until && !status.is_recovered)
    .map(([muscle, status]) => ({
      muscle,
      recoveryTime: new Date(status.recovery_until!),
      hoursRemaining: status.hours_until_recovery
    }))
    .sort((a, b) => a.recoveryTime.getTime() - b.recoveryTime.getTime());
};
```

### Format Hours Until Recovery

```typescript
const formatRecoveryTime = (hours: number): string => {
  if (hours === 0) return 'Recovered';
  if (hours < 1) return `${Math.round(hours * 60)} minutes`;
  if (hours < 24) return `${Math.round(hours)} hours`;
  const days = Math.floor(hours / 24);
  const remainingHours = Math.round(hours % 24);
  return `${days}d ${remainingHours}h`;
};
```

---

## Error Handling

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

---

## Notes

1. **All muscle groups are always returned** - Even if a muscle has no recovery data, it will be included with default values (fully recovered).

2. **Recovery status is updated automatically** - The endpoint calls `update_recovery_status()` which checks if `recovery_until` has passed.

3. **Fatigue accumulates per workout** - Each completed workout creates new recovery records. The endpoint returns the most recent recovery record for each muscle.

4. **Recovery percentage calculation** - Based on time elapsed since workout vs. total recovery time needed.

5. **Hours until recovery** - Calculated dynamically based on current time and `recovery_until` timestamp.

6. **Source workout** - Links recovery to the specific workout that caused the fatigue.

7. **Timestamp** - Server timestamp when the response was generated, useful for caching or showing "last updated" info.

---

## Example Usage Scenarios

### Scenario 1: Check if chest is ready for training
```typescript
const chestStatus = recoveryStatus.chest;
const canTrainChest = chestStatus.is_recovered || chestStatus.recovery_percentage >= 90;
```

### Scenario 2: Get next muscle to recover
```typescript
const nextToRecover = Object.entries(recoveryStatus)
  .filter(([_, s]) => !s.is_recovered)
  .sort(([_, a], [__, b]) => a.hours_until_recovery - b.hours_until_recovery)[0];
```

### Scenario 3: Count muscles in different recovery states
```typescript
const stats = {
  fullyRecovered: Object.values(recoveryStatus).filter(s => s.is_recovered).length,
  recovering: Object.values(recoveryStatus).filter(s => !s.is_recovered).length,
  highFatigue: Object.values(recoveryStatus).filter(s => s.fatigue_score > 3).length
};
```
