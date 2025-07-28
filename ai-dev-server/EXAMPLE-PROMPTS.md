# EXAMPLE-PROMPTS.md

## DETAILED PROMPT

Create a comprehensive **Intelligent Customer Support Automation System** workflow that processes customer inquiries through multiple AI-powered decision paths. Here's what I need:

**Workflow Requirements:**
1. **Webhook Trigger** - Accepts incoming customer support requests with fields: customer_email, subject, message, urgency_level, and customer_tier (basic/premium/enterprise)

2. **AI Analysis Phase** - Use OpenAI to analyze the incoming message for:
   - Sentiment classification (positive, neutral, negative, urgent)
   - Category classification (technical issue, billing question, feature request, complaint, compliment)
   - Urgency score (1-10 scale)
   - Required expertise level (tier-1, tier-2, specialist)

3. **Customer Data Enrichment** - Make HTTP requests to:
   - A CRM API to fetch customer history and subscription details
   - A knowledge base API to search for similar resolved tickets
   - Set nodes to merge and structure all collected data

4. **Multi-Branch Logic** - Create conditional paths using IF nodes:
   - **HIGH URGENCY PATH** (urgency > 7 OR sentiment = urgent OR customer_tier = enterprise)
   - **STANDARD PATH** (normal processing)
   - **POSITIVE FEEDBACK PATH** (sentiment = positive AND category = compliment)

5. **Database Operations** - Log everything to Google Sheets with columns for: timestamp, customer_email, category, sentiment, urgency_score, assigned_tier, resolution_status, response_time

6. **Intelligent Response System**:
   - **High Urgency**: Immediately create Slack alert, send escalation email to senior support, and auto-respond with priority acknowledgment
   - **Standard**: Generate AI-powered response using OpenAI based on knowledge base results, send standard acknowledgment email
   - **Positive Feedback**: Send thank-you email, update customer satisfaction metrics, notify sales team for upsell opportunity

7. **Follow-up Automation** - Set up delayed workflow triggers for:
   - 24-hour follow-up if no resolution marked
   - Customer satisfaction survey after resolution
   - Internal performance metrics update

8. **Error Handling** - Include proper error handling nodes that catch API failures and route to manual review queue

**Additional Requirements:**
- Use Set nodes to clean and transform data between each major step
- Include webhook response nodes to acknowledge receipt immediately
- Add time/date formatting for proper logging
- Use HTTP Request nodes for all external API calls
- Include email template personalization based on customer tier and sentiment
- Make the workflow production-ready with proper error handling and logging

The final workflow should demonstrate enterprise-level automation combining AI intelligence, multi-system integration, conditional logic, and comprehensive data management - showing how AI can completely transform customer support operations from reactive to proactive and intelligent.