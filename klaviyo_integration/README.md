# Klaviyo Integration for Odoo 19

## Overview

This module integrates Odoo Helpdesk with Klaviyo to send events when tickets are resolved. Events trigger Klaviyo flows which can send emails and generate coupons via Shopify.

## Features

- **Send events to Klaviyo** when helpdesk tickets are resolved
- **Three event types supported:**
  - `complaint_resolved` - When a customer complaint is resolved
  - `delivery_delay_confirmed` - When a delivery delay is confirmed
  - `goodwill_approved` - When goodwill compensation is approved
- **Event logging** - All API calls are logged for debugging
- **Retry mechanism** - Failed events are automatically retried via cron job
- **Goodwill amount tracking** - Track compensation amounts for goodwill events
- **Coupon code support** - Pass coupon codes to Klaviyo for email flows

## Installation

1. Copy the `klaviyo_integration` folder to your Odoo addons directory:
   ```
   /odoo/addons/klaviyo_integration/
   ```

2. Update the addons list:
   - Go to Apps
   - Click "Update Apps List"

3. Install the module:
   - Search for "Klaviyo Integration"
   - Click Install

## Configuration

1. Go to **Settings → Klaviyo**

2. Configure:
   - **Enable Klaviyo Integration**: Turn on/off the integration
   - **API Key**: Enter your Klaviyo Private API Key
   - **API Revision**: Set the API revision date (default: 2024-02-15)

### Getting Your Klaviyo API Key

1. Log into Klaviyo
2. Go to Account → Settings → API Keys
3. Create a new Private API Key
4. Copy the key to Odoo settings

## Usage

### Resolving a Ticket with Klaviyo Event

1. Open a Helpdesk Ticket
2. Go to the **Klaviyo** tab
3. Select a **Resolution Type**:
   - Complaint Resolved
   - Delivery Delay Confirmed
   - Goodwill Approved
4. (Optional) Enter **Goodwill Amount** if applicable
5. (Optional) Enter **Coupon Code** if pre-generated
6. Click **"Resolve & Send to Klaviyo"** button

### Manual Event Sending

If you need to resend an event:
1. Open the ticket
2. Click **"Send Klaviyo Event"** button

### Viewing Event Logs

1. Go to **Helpdesk → Reporting → Klaviyo Events**
2. View all sent events with status
3. Click on an event to see full payload and response

## Event Payload

The following data is sent to Klaviyo:

```json
{
  "data": {
    "type": "event",
    "attributes": {
      "metric": {
        "data": {
          "type": "metric",
          "attributes": {
            "name": "Complaint Resolved"
          }
        }
      },
      "profile": {
        "data": {
          "type": "profile",
          "attributes": {
            "email": "customer@example.com",
            "first_name": "John",
            "last_name": "Doe"
          }
        }
      },
      "properties": {
        "ticket_id": 123,
        "ticket_name": "TICKET-001",
        "resolution_type": "complaint_resolved",
        "resolution_date": "2026-03-01T10:00:00",
        "order_id": 456,
        "order_name": "S00123",
        "goodwill_amount": 50.00,
        "coupon_code": "SORRY20"
      }
    }
  }
}
```

## Setting Up Klaviyo Flows

In Klaviyo, create flows triggered by these metrics:
- **Complaint Resolved**
- **Delivery Delay Confirmed**
- **Goodwill Approved**

Each flow can:
- Send personalized email to customer
- Trigger Shopify coupon generation (via Klaviyo-Shopify integration)
- Add customer to specific segments

## Coupon Generation

Coupons should be generated in Shopify via Klaviyo flows:
1. Set up Klaviyo-Shopify integration
2. In your Klaviyo flow, add a "Generate Coupon" action
3. Configure:
   - Single use
   - Expiry date
   - Minimum spend requirement

## Troubleshooting

### Events Not Sending

1. Check if integration is enabled in Settings
2. Verify API key is correct
3. Check event logs for error messages
4. Ensure customer has valid email

### API Errors

Common error codes:
- **401**: Invalid API key
- **400**: Invalid payload (check customer email)
- **429**: Rate limited (wait and retry)

## Dependencies

- `helpdesk` - Odoo Helpdesk module
- `sale` - Odoo Sales module
- `base` - Odoo Base

## Support

For issues or feature requests, contact your Odoo administrator.
