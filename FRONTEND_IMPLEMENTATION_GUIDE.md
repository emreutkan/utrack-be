# Frontend Implementation Guide

## Overview

This guide documents all API changes and new features that require frontend updates. Use this to understand what changed, what's new, and how to implement these changes in your frontend application.

## Table of Contents

1. [Breaking Changes](#breaking-changes)
2. [New Features](#new-features)
3. [API Response Format Changes](#api-response-format-changes)
4. [Pagination Updates](#pagination-updates)
5. [Error Handling Updates](#error-handling-updates)
6. [New Endpoints](#new-endpoints)
7. [Email Functionality](#email-functionality)
8. [Validation Updates](#validation-updates)
9. [Implementation Checklist](#implementation-checklist)

---

## Breaking Changes

### 1. Error Response Format Standardized

**Before:**
```json
{
  "error": "User supplement not found"
}
```

**After:**
```json
{
  "error": "NOT_FOUND",
  "message": "The requested resource was not found.",
  "details": {
    "error": "User supplement not found"
  }
}
```

**Action Required:**
- Update all error handling code to check for `error` field (error code)
- Display `message` field to users (user-friendly message)
- Use `details` field for additional error information if needed

**Example:**
```javascript
// Old way
catch (error) {
  if (error.response?.data?.error) {
    showError(error.response.data.error);
  }
}

// New way
catch (error) {
  const errorData = error.response?.data;
  if (errorData) {
    showError(errorData.message); // User-friendly message
    console.error('Error code:', errorData.error); // For debugging
    if (errorData.details) {
      // Handle specific validation errors
      handleValidationErrors(errorData.details);
    }
  }
}
```

---

## New Features

### 1. Password Reset Email Functionality

**What Changed:**
- Password reset now sends actual emails instead of returning tokens in response
- Email templates are HTML and plain text

**Frontend Implementation:**

**Request Password Reset:**
```javascript
// POST /api/user/request-password-reset/
const requestPasswordReset = async (email) => {
  try {
    const response = await fetch('/api/user/request-password-reset/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });
    
    if (response.ok) {
      // Show success message (don't reveal if email exists for security)
      showMessage('If an account with this email exists, a password reset link has been sent.');
    }
  } catch (error) {
    handleError(error);
  }
};
```

**Reset Password Page:**
- Create a reset password page that accepts `uid` and `token` from URL query parameters
- Example URL: `https://yourfrontend.com/reset-password?uid=MTIz&token=abc123xyz`

```javascript
// Extract from URL
const urlParams = new URLSearchParams(window.location.search);
const uid = urlParams.get('uid');
const token = urlParams.get('token');

// POST /api/user/reset-password/
const resetPassword = async (newPassword) => {
  try {
    const response = await fetch('/api/user/reset-password/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        uid,
        token,
        new_password: newPassword,
      }),
    });
    
    if (response.ok) {
      showMessage('Password reset successfully!');
      redirectToLogin();
    } else {
      const error = await response.json();
      showError(error.message);
    }
  } catch (error) {
    handleError(error);
  }
};
```

**Email Link Format:**
- The backend generates links in format: `{FRONTEND_URL}/reset-password?uid={uid}&token={token}`
- Ensure your frontend URL is set in backend's `FRONTEND_URL` environment variable

---

### 2. Health Check Endpoint

**New Endpoint:**
```
GET /api/health/
```

**Purpose:** Monitor API health, database connectivity, and cache status

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "cache": {
      "status": "healthy",
      "message": "Cache connection successful"
    }
  },
  "environment": {
    "debug": false,
    "timezone": "UTC"
  }
}
```

**Frontend Implementation:**
```javascript
// Check API health (useful for status pages or monitoring)
const checkApiHealth = async () => {
  try {
    const response = await fetch('/api/health/');
    const data = await response.json();
    
    if (data.status === 'healthy') {
      return { healthy: true, checks: data.checks };
    } else {
      return { healthy: false, checks: data.checks };
    }
  } catch (error) {
    return { healthy: false, error: error.message };
  }
};

// Use in status page or monitoring dashboard
const apiStatus = await checkApiHealth();
if (!apiStatus.healthy) {
  showWarning('API is experiencing issues');
}
```

---

## API Response Format Changes

### Standardized Error Format

All API errors now follow this format:

```json
{
  "error": "ERROR_CODE",
  "message": "User-friendly error message",
  "details": {
    // Additional error details (optional)
    // For validation errors, this contains field-specific errors
  }
}
```

**Common Error Codes:**
- `BAD_REQUEST` - 400
- `UNAUTHORIZED` - 401
- `FORBIDDEN` - 403
- `NOT_FOUND` - 404
- `VALIDATION_ERROR` - 422
- `TOO_MANY_REQUESTS` - 429
- `INTERNAL_SERVER_ERROR` - 500

**Update Your Error Handler:**
```javascript
// Create a centralized error handler
const handleApiError = (error) => {
  const errorData = error.response?.data;
  
  if (!errorData) {
    return 'An unexpected error occurred';
  }
  
  // Use the user-friendly message
  return errorData.message || 'An error occurred';
  
  // Optional: Handle specific error codes
  switch (errorData.error) {
    case 'UNAUTHORIZED':
      redirectToLogin();
      break;
    case 'FORBIDDEN':
      showUpgradePrompt(); // For PRO features
      break;
    case 'TOO_MANY_REQUESTS':
      showRateLimitMessage();
      break;
  }
};
```

---

## Pagination Updates

### New Paginated Endpoints

The following endpoints now return paginated responses:

1. **Supplements List** - `GET /api/supplements/list/`
2. **User Supplements** - `GET /api/supplements/user/list/`
3. **Body Measurements** - `GET /api/measurements/`
4. **Achievements List** - `GET /api/achievements/list/`
5. **Leaderboard** - `GET /api/achievements/leaderboard/<exercise_id>/`

### Pagination Response Format

**Before (non-paginated):**
```json
[
  { "id": 1, "name": "Item 1" },
  { "id": 2, "name": "Item 2" }
]
```

**After (paginated):**
```json
{
  "count": 100,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [
    { "id": 1, "name": "Item 1" },
    { "id": 2, "name": "Item 2" }
  ]
}
```

### Frontend Implementation

**Update List Components:**
```javascript
// Old way (direct array)
const [supplements, setSupplements] = useState([]);

useEffect(() => {
  fetch('/api/supplements/list/')
    .then(res => res.json())
    .then(data => setSupplements(data));
}, []);

// New way (paginated)
const [supplements, setSupplements] = useState([]);
const [pagination, setPagination] = useState({
  count: 0,
  next: null,
  previous: null,
  page: 1,
  pageSize: 50
});

const fetchSupplements = async (page = 1, pageSize = 50) => {
  try {
    const response = await fetch(
      `/api/supplements/list/?page=${page}&page_size=${pageSize}`
    );
    const data = await response.json();
    
    setSupplements(data.results);
    setPagination({
      count: data.count,
      next: data.next,
      previous: data.previous,
      page,
      pageSize
    });
  } catch (error) {
    handleError(error);
  }
};

useEffect(() => {
  fetchSupplements();
}, []);
```

**Pagination Controls:**
```jsx
// React example
const PaginationControls = ({ pagination, onPageChange }) => {
  const totalPages = Math.ceil(pagination.count / pagination.pageSize);
  
  return (
    <div className="pagination">
      <button 
        disabled={!pagination.previous}
        onClick={() => onPageChange(pagination.page - 1)}
      >
        Previous
      </button>
      
      <span>
        Page {pagination.page} of {totalPages}
      </span>
      
      <button 
        disabled={!pagination.next}
        onClick={() => onPageChange(pagination.page + 1)}
      >
        Next
      </button>
      
      <select 
        value={pagination.pageSize}
        onChange={(e) => onPageChange(1, parseInt(e.target.value))}
      >
        <option value={20}>20 per page</option>
        <option value={50}>50 per page</option>
        <option value={100}>100 per page</option>
      </select>
    </div>
  );
};
```

**Page Size Limits:**
- Supplements: max 200 per page (default: 50)
- Body Measurements: max 100 per page (default: 30)
- Achievements: max 100 per page (default: 20)

---

## Error Handling Updates

### Validation Error Format

Validation errors now include detailed field information:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Validation error. Please check your input.",
  "details": {
    "dosage": ["Dosage must be greater than 0."],
    "frequency": ["Frequency must be one of: daily, weekly, custom"]
  }
}
```

**Frontend Implementation:**
```javascript
const handleValidationErrors = (details) => {
  const fieldErrors = {};
  
  // Extract field-specific errors
  Object.keys(details).forEach(field => {
    if (Array.isArray(details[field])) {
      fieldErrors[field] = details[field][0]; // Get first error
    } else if (typeof details[field] === 'string') {
      fieldErrors[field] = details[field];
    }
  });
  
  return fieldErrors;
};

// Use in form
const submitForm = async (formData) => {
  try {
    const response = await fetch('/api/endpoint/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      if (error.error === 'VALIDATION_ERROR' && error.details) {
        // Set field-specific errors
        const fieldErrors = handleValidationErrors(error.details);
        setFormErrors(fieldErrors);
      } else {
        // Show general error
        showError(error.message);
      }
    }
  } catch (error) {
    handleError(error);
  }
};
```

---

## New Endpoints

### Health Check

```
GET /api/health/
```

**Authentication:** Not required (public endpoint)

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "cache": {
      "status": "healthy",
      "message": "Cache connection successful"
    }
  },
  "environment": {
    "debug": false,
    "timezone": "UTC"
  }
}
```

**Use Cases:**
- Status page
- Monitoring dashboard
- Pre-flight checks before API calls
- Health indicators in admin panels

---

## Email Functionality

### Password Reset Flow

**Step 1: Request Reset**
```javascript
POST /api/user/request-password-reset/
Body: { "email": "user@example.com" }

Response: {
  "message": "If an account with this email exists, a password reset link has been sent."
}
```

**Step 2: User Clicks Email Link**
- Email contains link: `{FRONTEND_URL}/reset-password?uid={uid}&token={token}`
- Frontend should extract `uid` and `token` from URL

**Step 3: Reset Password**
```javascript
POST /api/user/reset-password/
Body: {
  "uid": "MTIz",
  "token": "abc123xyz",
  "new_password": "newSecurePassword123"
}

Success Response: {
  "message": "Password reset successfully"
}

Error Response: {
  "error": "BAD_REQUEST",
  "message": "Invalid or expired reset token"
}
```

**Frontend Implementation:**
```jsx
// ResetPasswordPage.jsx
import { useSearchParams, useNavigate } from 'react-router-dom';

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const uid = searchParams.get('uid');
  const token = searchParams.get('token');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await fetch('/api/user/reset-password/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uid,
          token,
          new_password: password,
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        showSuccess('Password reset successfully!');
        navigate('/login');
      } else {
        setError(data.message || 'Failed to reset password');
      }
    } catch (error) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  if (!uid || !token) {
    return <div>Invalid reset link</div>;
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="New Password"
        required
      />
      <input
        type="password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        placeholder="Confirm Password"
        required
      />
      {error && <div className="error">{error}</div>}
      <button type="submit" disabled={loading}>
        {loading ? 'Resetting...' : 'Reset Password'}
      </button>
    </form>
  );
};
```

---

## Validation Updates

### New Validation Rules

**Supplements:**
- Dosage: Must be positive, max 10000
- Frequency: Must be one of: `daily`, `weekly`, `custom`
- Date: Cannot be in the future
- Time: Cannot be in the future if date is today

**Body Measurements:**
- Height: 50-300 cm
- Weight: 20-500 kg
- Waist: 30-200 cm
- Neck: 20-80 cm
- Hips: 50-200 cm (required for women)
- Cross-validation: Waist must be greater than neck

**Frontend Validation (Client-Side):**
```javascript
// Supplements validation
const validateSupplementDosage = (dosage) => {
  if (dosage <= 0) {
    return 'Dosage must be greater than 0';
  }
  if (dosage > 10000) {
    return 'Dosage is too high. Please check your input.';
  }
  return null;
};

const validateSupplementDate = (date) => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const selectedDate = new Date(date);
  
  if (selectedDate > today) {
    return 'Date cannot be in the future';
  }
  return null;
};

// Body measurements validation
const validateBodyMeasurement = (data) => {
  const errors = {};
  
  if (data.height < 50 || data.height > 300) {
    errors.height = 'Height must be between 50 and 300 cm';
  }
  
  if (data.weight < 20 || data.weight > 500) {
    errors.weight = 'Weight must be between 20 and 500 kg';
  }
  
  if (data.waist < 30 || data.waist > 200) {
    errors.waist = 'Waist must be between 30 and 200 cm';
  }
  
  if (data.neck < 20 || data.neck > 80) {
    errors.neck = 'Neck must be between 20 and 80 cm';
  }
  
  if (data.gender === 'female' && (!data.hips || data.hips < 50 || data.hips > 200)) {
    errors.hips = 'Hips must be between 50 and 200 cm (required for women)';
  }
  
  // Cross-validation
  if (data.waist && data.neck && data.waist <= data.neck) {
    errors.waist = 'Waist must be greater than neck measurement';
  }
  
  return errors;
};
```

---

## Implementation Checklist

### Critical Updates (Required)

- [ ] **Update error handling** to use new standardized error format
  - Check for `error` (code), `message` (user-friendly), `details` (additional info)
  
- [ ] **Add pagination** to all list endpoints:
  - Supplements list
  - User supplements list
  - Body measurements list
  - Achievements list
  
- [ ] **Update password reset flow**:
  - Remove token display (no longer returned)
  - Add email input form
  - Create reset password page that accepts `uid` and `token` from URL
  - Handle new error format

### Recommended Updates

- [ ] **Add health check** to status page or monitoring
- [ ] **Update validation** to match new backend rules
- [ ] **Improve error messages** using new `message` field
- [ ] **Add loading states** for paginated lists
- [ ] **Update API client** to handle pagination automatically

### Optional Enhancements

- [ ] Add page size selector for paginated lists
- [ ] Add infinite scroll for better UX
- [ ] Show API health status in admin panel
- [ ] Add retry logic for failed requests
- [ ] Implement optimistic updates where appropriate

---

## Migration Guide

### Step-by-Step Migration

**1. Update Error Handling (Day 1)**
```javascript
// Create new error handler utility
// Update all catch blocks to use new format
// Test all error scenarios
```

**2. Add Pagination (Day 2-3)**
```javascript
// Update list components
// Add pagination controls
// Test with different page sizes
```

**3. Update Password Reset (Day 4)**
```javascript
// Create reset password page
// Update request reset flow
// Test email link handling
```

**4. Add Health Check (Day 5)**
```javascript
// Add to status page
// Optional: Add to monitoring dashboard
```

**5. Update Validation (Ongoing)**
```javascript
// Add client-side validation
// Match backend rules
// Improve user feedback
```

---

## Testing Checklist

After implementing changes, test:

- [ ] Error handling displays user-friendly messages
- [ ] Pagination works on all list endpoints
- [ ] Page size changes work correctly
- [ ] Password reset email flow works end-to-end
- [ ] Reset password page handles invalid tokens
- [ ] Validation errors show field-specific messages
- [ ] Health check endpoint is accessible
- [ ] All existing features still work

---

## Support

If you encounter issues during implementation:

1. Check the API documentation: `/api/docs/`
2. Review error responses for detailed messages
3. Check network tab for actual API responses
4. Verify environment variables are set correctly

---

## Version Information

- **Backend Version:** Updated with comprehensive improvements
- **API Version:** Compatible with existing endpoints (no versioning yet)
- **Breaking Changes:** Error format only (backward compatible with proper handling)

---

## Quick Reference

### Error Codes
- `BAD_REQUEST` - Check your input
- `UNAUTHORIZED` - Login required
- `FORBIDDEN` - Permission denied
- `NOT_FOUND` - Resource not found
- `VALIDATION_ERROR` - Check `details` for field errors
- `TOO_MANY_REQUESTS` - Rate limit exceeded

### Pagination Query Params
- `page` - Page number (default: 1)
- `page_size` - Items per page (varies by endpoint)

### New Endpoints
- `GET /api/health/` - Health check (no auth required)

### Updated Endpoints
- All list endpoints now return paginated responses
- All error responses now use standardized format
