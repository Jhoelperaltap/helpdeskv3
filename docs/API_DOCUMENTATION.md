# Helpdesk API Documentation

## Overview

The Helpdesk API provides a comprehensive REST interface for managing tickets, users, categories, tags, and other helpdesk resources. The API follows RESTful principles and uses JSON for data exchange.

## Base URL

\`\`\`
https://your-domain.com/api/v1/
\`\`\`

## Authentication

The API uses JWT (JSON Web Token) authentication. To access protected endpoints, you need to:

1. Obtain a token by sending credentials to `/api/v1/auth/token/`
2. Include the token in the Authorization header: `Authorization: Bearer <token>`

### Authentication Endpoints

- `POST /api/v1/auth/token/` - Obtain access and refresh tokens
- `POST /api/v1/auth/token/refresh/` - Refresh access token
- `POST /api/v1/auth/token/verify/` - Verify token validity

## API Endpoints

### Tickets

#### List Tickets
\`\`\`http
GET /api/v1/tickets/
\`\`\`

**Query Parameters:**
- `status` - Filter by status (open, in_progress, resolved, closed)
- `priority` - Filter by priority (low, medium, high, urgent)
- `category` - Filter by category ID
- `assigned_to` - Filter by assigned user ID
- `created_by` - Filter by creator user ID
- `tags` - Filter by tag ID
- `search` - Search in title, description, and comments
- `ordering` - Order by field (created_at, updated_at, priority, due_date)
- `page` - Page number for pagination
- `page_size` - Number of items per page (default: 20)

**Response:**
\`\`\`json
{
  "count": 150,
  "next": "http://api.example.com/api/v1/tickets/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Login issue",
      "status": "open",
      "status_display": "Open",
      "priority": "high",
      "priority_display": "High",
      "assigned_to": {
        "id": 2,
        "username": "tech1",
        "email": "tech1@example.com"
      },
      "category": {
        "id": 1,
        "name": "Technical",
        "color": "#007bff"
      },
      "tags": [
        {
          "id": 1,
          "name": "login",
          "color": "#28a745"
        }
      ],
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:00:00Z",
      "due_date": "2024-01-16T17:00:00Z",
      "time_since_created": "2 hours ago",
      "comment_count": 3
    }
  ]
}
\`\`\`

#### Get Ticket Details
\`\`\`http
GET /api/v1/tickets/{id}/
\`\`\`

#### Create Ticket
\`\`\`http
POST /api/v1/tickets/
\`\`\`

**Request Body:**
\`\`\`json
{
  "title": "New ticket title",
  "description": "Detailed description of the issue",
  "priority": "medium",
  "category": 1,
  "assigned_to": 2,
  "due_date": "2024-01-20T17:00:00Z",
  "tags": [1, 2]
}
\`\`\`

#### Update Ticket
\`\`\`http
PUT /api/v1/tickets/{id}/
PATCH /api/v1/tickets/{id}/
\`\`\`

#### Delete Ticket
\`\`\`http
DELETE /api/v1/tickets/{id}/
\`\`\`

#### Ticket Actions

##### Assign Ticket
\`\`\`http
POST /api/v1/tickets/{id}/assign/
\`\`\`

**Request Body:**
\`\`\`json
{
  "user_id": 2
}
\`\`\`

##### Change Status
\`\`\`http
POST /api/v1/tickets/{id}/change_status/
\`\`\`

**Request Body:**
\`\`\`json
{
  "status": "resolved",
  "resolution": "Issue resolved by updating configuration"
}
\`\`\`

##### Get Ticket Statistics
\`\`\`http
GET /api/v1/tickets/stats/
\`\`\`

**Response:**
\`\`\`json
{
  "total_tickets": 150,
  "open_tickets": 45,
  "in_progress_tickets": 30,
  "resolved_tickets": 60,
  "closed_tickets": 15,
  "overdue_tickets": 8,
  "tickets_by_priority": {
    "low": 20,
    "medium": 80,
    "high": 40,
    "urgent": 10
  },
  "tickets_by_category": {
    "Technical": 80,
    "Billing": 30,
    "General": 40
  },
  "avg_resolution_time": 24.5,
  "tickets_created_today": 5,
  "tickets_resolved_today": 8
}
\`\`\`

##### Get My Tickets
\`\`\`http
GET /api/v1/tickets/my_tickets/
\`\`\`

### Comments

#### List Ticket Comments
\`\`\`http
GET /api/v1/tickets/{ticket_id}/comments/
\`\`\`

#### Create Comment
\`\`\`http
POST /api/v1/tickets/{ticket_id}/comments/
\`\`\`

**Request Body:**
\`\`\`json
{
  "content": "This is a comment on the ticket",
  "is_internal": false
}
\`\`\`

#### Update Comment
\`\`\`http
PUT /api/v1/tickets/{ticket_id}/comments/{id}/
PATCH /api/v1/tickets/{ticket_id}/comments/{id}/
\`\`\`

#### Delete Comment
\`\`\`http
DELETE /api/v1/tickets/{ticket_id}/comments/{id}/
\`\`\`

### Categories

#### List Categories
\`\`\`http
GET /api/v1/categories/
\`\`\`

#### Create Category
\`\`\`http
POST /api/v1/categories/
\`\`\`

**Request Body:**
\`\`\`json
{
  "name": "New Category",
  "description": "Category description",
  "color": "#007bff"
}
\`\`\`

### Tags

#### List Tags
\`\`\`http
GET /api/v1/tags/
\`\`\`

#### Get Popular Tags
\`\`\`http
GET /api/v1/tags/popular/
\`\`\`

#### Create Tag
\`\`\`http
POST /api/v1/tags/
\`\`\`

**Request Body:**
\`\`\`json
{
  "name": "urgent",
  "color": "#dc3545",
  "description": "Urgent issues requiring immediate attention"
}
\`\`\`

### Response Templates

#### List Templates
\`\`\`http
GET /api/v1/templates/
\`\`\`

#### Create Template
\`\`\`http
POST /api/v1/templates/
\`\`\`

**Request Body:**
\`\`\`json
{
  "title": "Welcome Message",
  "content": "Hello {customer_name}, thank you for contacting us regarding {issue_type}.",
  "category": "greeting",
  "is_public": true,
  "variables": ["customer_name", "issue_type"]
}
\`\`\`

#### Use Template
\`\`\`http
POST /api/v1/templates/{id}/use_template/
\`\`\`

**Request Body:**
\`\`\`json
{
  "context": {
    "customer_name": "John Doe",
    "issue_type": "login problem"
  }
}
\`\`\`

**Response:**
\`\`\`json
{
  "processed_content": "Hello John Doe, thank you for contacting us regarding login problem.",
  "original_content": "Hello {customer_name}, thank you for contacting us regarding {issue_type}.",
  "variables": ["customer_name", "issue_type"]
}
\`\`\`

### Users

#### List Users
\`\`\`http
GET /api/v1/users/
\`\`\`

### Saved Filters

#### List Saved Filters
\`\`\`http
GET /api/v1/filters/
\`\`\`

#### Create Saved Filter
\`\`\`http
POST /api/v1/filters/
\`\`\`

**Request Body:**
\`\`\`json
{
  "name": "High Priority Open Tickets",
  "filter_params": {
    "status": "open",
    "priority": "high"
  },
  "is_public": false
}
\`\`\`

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format:

\`\`\`json
{
  "error": "Validation failed",
  "details": {
    "title": ["This field is required."],
    "priority": ["Invalid choice."]
  }
}
\`\`\`

## Rate Limiting

API requests are rate-limited to prevent abuse:
- Authenticated users: 1000 requests per hour
- Anonymous users: 100 requests per hour

## Pagination

List endpoints support pagination with the following parameters:
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

## Filtering and Searching

Most list endpoints support:
- **Filtering**: Use query parameters to filter results
- **Searching**: Use the `search` parameter for full-text search
- **Ordering**: Use the `ordering` parameter to sort results

## WebSocket Support

Real-time updates are available via WebSocket connections:
- Connect to: `ws://your-domain.com/ws/notifications/`
- Authentication: Include JWT token in connection headers

## SDK and Examples

### Python Example

\`\`\`python
import requests

# Authenticate
response = requests.post('https://api.example.com/api/v1/auth/token/', {
    'username': 'your_username',
    'password': 'your_password'
})
token = response.json()['access']

# Make authenticated request
headers = {'Authorization': f'Bearer {token}'}
tickets = requests.get('https://api.example.com/api/v1/tickets/', headers=headers)
print(tickets.json())
\`\`\`

### JavaScript Example

\`\`\`javascript
// Authenticate
const authResponse = await fetch('/api/v1/auth/token/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'your_username',
    password: 'your_password'
  })
});
const { access } = await authResponse.json();

// Make authenticated request
const ticketsResponse = await fetch('/api/v1/tickets/', {
  headers: { 'Authorization': `Bearer ${access}` }
});
const tickets = await ticketsResponse.json();
console.log(tickets);
\`\`\`

## Support

For API support and questions, please contact the development team or refer to the interactive API documentation at `/api/docs/`.
