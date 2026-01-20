# PRO vs FREE Endpoints Analysis

## Currently PRO-ONLY Endpoints

### Workout Endpoints
1. **`GET /api/workout/recommendations/recovery/`** - Recovery recommendations based on last workout
   - Full PRO check with 403 response
   
2. **`GET /api/workout/exercise/<workout_exercise_id>/rest-recommendations/`** - Rest period recommendations
   - Full PRO check with 403 response
   
3. **`GET /api/workout/recommendations/frequency/`** - Training frequency recommendations
   - Full PRO check with 403 response

## Currently FREE (with PRO features)

### Workout Endpoints
1. **`GET /api/workout/volume-analysis/`** - Volume analysis per muscle group
   - FREE: Limited to 4 weeks
   - PRO: Unlimited weeks
   
2. **`GET /api/workout/<workout_id>/summary/`** - Workout summary with scoring
   - FREE: Basic recovery analysis only
   - PRO: Includes 1RM performance analysis
   
3. **`GET /api/workout/recovery/status/`** - Muscle recovery status
   - FREE: Basic muscle recovery only
   - PRO: Includes CNS recovery data

4. **`GET /api/workout/research/`** - Research articles
   - Currently FREE for all users (no pro check)

## Currently FREE Endpoints (No PRO restrictions)

### Workout Endpoints
- `POST /api/workout/create/` - Create workout
- `GET /api/workout/list/` - List workouts
- `GET /api/workout/list/<workout_id>/` - Get specific workout
- `POST /api/workout/<workout_id>/add_exercise/` - Add exercise to workout
- `POST /api/workout/exercise/<workout_exercise_id>/add_set/` - Add set
- `GET /api/workout/active/` - Get active workout
- `GET /api/workout/active/rest-timer/` - Get rest timer state
- `POST /api/workout/active/rest-timer/stop/` - Stop rest timer
- `POST /api/workout/active/rest-timer/resume/` - Resume rest timer
- `POST /api/workout/<workout_id>/update/` - Update workout
- `POST /api/workout/<workout_id>/complete/` - Complete workout
- `POST /api/workout/<workout_id>/delete/` - Delete workout
- `POST /api/workout/<workout_id>/update_order/` - Update exercise order
- `PUT /api/workout/set/<int:set_id>/update/` - Update set
- `DELETE /api/workout/set/<int:set_id>/delete/` - Delete set
- `DELETE /api/workout/exercise/<workout_exercise_id>/delete/` - Delete exercise
- `GET /api/workout/calendar/` - Calendar view
- `GET /api/workout/calendar/stats/` - Calendar stats
- `GET /api/workout/years/` - Available years
- `GET /api/workout/exercise/<exercise_id>/1rm-history/` - 1RM history
- `GET /api/workout/exercise/<exercise_id>/set-history/` - Set history
- `GET /api/workout/check-today/` - Check if worked out today
- `POST /api/workout/template/create/` - Create template
- `GET /api/workout/template/list/` - List templates
- `DELETE /api/workout/template/delete/<template_id>/` - Delete template
- `POST /api/workout/template/start/` - Start template workout

### Achievement Endpoints (All FREE)
- `GET /api/achievements/list/` - List all achievements
- `GET /api/achievements/earned/` - User's earned achievements
- `GET /api/achievements/categories/` - Achievement categories
- `GET /api/achievements/unnotified/` - Unnotified achievements
- `POST /api/achievements/unnotified/mark-seen/` - Mark as seen
- `GET /api/achievements/prs/` - Personal records list
- `GET /api/achievements/prs/<exercise_id>/` - PR detail
- `GET /api/achievements/stats/` - User statistics
- `POST /api/achievements/recalculate/` - Recalculate stats
- `GET /api/achievements/ranking/<exercise_id>/` - Exercise ranking
- `GET /api/achievements/rankings/` - All rankings
- `GET /api/achievements/leaderboard/<exercise_id>/` - Leaderboard

### User Endpoints (All FREE)
- `POST /api/user/register/` - Register
- `GET /api/user/me/` - User profile
- `POST /api/user/height/` - Update height
- `POST /api/user/weight/` - Update weight
- `GET /api/user/weight/history/` - Weight history
- `DELETE /api/user/weight/<weight_id>/` - Delete weight entry
- `POST /api/user/gender/` - Update gender
- `POST /api/user/change-password/` - Change password
- `POST /api/user/request-password-reset/` - Request password reset
- `POST /api/user/reset-password/` - Reset password
- `POST /api/user/check-email/` - Check email
- `POST /api/user/check-password/` - Check password
- `POST /api/user/check-name/` - Check name
- `POST /api/user/login/` - Login
- `POST /api/user/refresh/` - Refresh token
- `GET /api/user/data/export/` - Export data
- `POST /api/user/data/import/` - Import data

### Exercise Endpoints (All FREE)
- `GET /api/exercise/list/` - List exercises
- `POST /api/exercise/add/<workout_id>/` - Add exercise to workout

### Supplements Endpoints (All FREE)
- `GET /api/supplements/list/` - List supplements
- `GET /api/supplements/user/list/` - User's supplements
- `POST /api/supplements/user/add/` - Add supplement
- `GET /api/supplements/user/log/list/` - Supplement logs
- `POST /api/supplements/user/log/add/` - Add log entry
- `GET /api/supplements/user/log/today/` - Today's logs
- `DELETE /api/supplements/user/log/delete/<log_id>/` - Delete log

### Body Measurements Endpoints (All FREE)
- `GET /api/measurements/` - List measurements
- `POST /api/measurements/create/` - Create measurement
- `POST /api/measurements/calculate-body-fat/men/` - Calculate body fat (men)
- `POST /api/measurements/calculate-body-fat/women/` - Calculate body fat (women)

---

## Recommendations: What SHOULD be PRO-ONLY

### High Priority (Premium Features)
1. **`GET /api/workout/research/`** - Research articles
   - **Recommendation: PRO-ONLY**
   - Research-backed insights are premium value
   - Currently free but should be gated

2. **`GET /api/workout/exercise/<exercise_id>/1rm-history/`** - 1RM history
   - **Recommendation: PRO-ONLY or limit FREE to 30 days**
   - Advanced analytics feature
   - FREE could see last 30 days, PRO gets full history

3. **`GET /api/workout/exercise/<exercise_id>/set-history/`** - Set history
   - **Recommendation: PRO-ONLY or limit FREE to 30 days**
   - Detailed historical data
   - FREE could see last 30 days, PRO gets full history

4. **`GET /api/workout/volume-analysis/`** - Volume analysis
   - **Current: FREE limited to 4 weeks**
   - **Recommendation: Keep current or make fully PRO-ONLY**
   - Already has good limitation, could make fully PRO

5. **`GET /api/achievements/leaderboard/<exercise_id>/`** - Leaderboards
   - **Recommendation: PRO-ONLY**
   - Competitive/social feature, good premium value

6. **`GET /api/achievements/ranking/<exercise_id>/`** - Percentile rankings
   - **Recommendation: PRO-ONLY**
   - Advanced analytics, premium feature

7. **`GET /api/achievements/rankings/`** - All rankings
   - **Recommendation: PRO-ONLY**
   - Advanced analytics, premium feature

### Medium Priority (Nice-to-Have Premium)
8. **`GET /api/workout/calendar/stats/`** - Calendar stats
   - **Recommendation: FREE with basic stats, PRO gets advanced analytics**
   - Could show basic count for FREE, detailed breakdown for PRO

9. **`POST /api/workout/template/create/`** - Workout templates
   - **Recommendation: FREE limited to 3 templates, PRO unlimited**
   - Templates are useful but not critical
   - FREE users get 3, PRO gets unlimited

10. **`GET /api/user/data/export/`** - Data export
    - **Recommendation: PRO-ONLY**
    - Data portability is premium feature
    - FREE users can view but not export

11. **`POST /api/user/data/import/`** - Data import
    - **Recommendation: PRO-ONLY**
    - Data import is premium feature

### Low Priority (Keep FREE)
- Basic workout CRUD operations (create, list, update, delete)
- Basic achievement viewing
- Basic statistics
- Exercise list
- Supplements tracking
- Body measurements
- Basic recovery status (without CNS)

---

## Summary

**Currently PRO-ONLY: 3 endpoints**
- Recovery recommendations
- Rest period recommendations  
- Training frequency recommendations

**Currently FREE with PRO features: 4 endpoints**
- Volume analysis (4 week limit)
- Workout summary (1RM analysis for PRO)
- Recovery status (CNS for PRO)
- Research (currently free, should be PRO)

**Recommendations to make PRO-ONLY: 7-10 endpoints**
- Research articles
- 1RM history (or limit to 30 days for FREE)
- Set history (or limit to 30 days for FREE)
- Leaderboards
- Percentile rankings
- Data export/import
- Workout templates (limit to 3 for FREE)
