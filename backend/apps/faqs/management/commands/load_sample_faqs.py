from django.core.management.base import BaseCommand
from apps.faqs.models import FAQ
from apps.knowledge_base.services.ingestion_service import IngestionService

SAMPLE_FAQS = [
    {
        'category': 'General Information',
        'question': 'What is Nexora Technologies and what do you do?',
        'answer': 'Nexora Technologies is a modern enterprise software provider offering cloud-native automation, workflow management, and collaborative productivity tools designed to streamline team operations across global organizations.',
        'keywords': ['company', 'about', 'nexora', 'who are you', 'overview', 'mission', 'what do you do', 'what is nexora', 'background']
    },
    {
        'category': 'General Information',
        'question': 'What are your standard business hours?',
        'answer': 'Our corporate headquarters and customer care teams operate Monday through Friday, 8:00 AM to 8:00 PM Eastern Time (ET). Critical technical support services are monitored 24/7/365 for Enterprise tier clients.',
        'keywords': ['hours', 'business hours', 'operating hours', 'open', 'when are you open', 'schedule', 'time', 'work hours', 'timing']
    },
    {
        'category': 'General Information',
        'question': 'What is your service availability and uptime guarantee?',
        'answer': 'Nexora maintains a guaranteed 99.95% service uptime Service Level Agreement (SLA) for our production cloud infrastructure. Real-time platform status and historical incident logs can be reviewed anytime on our public status page.',
        'keywords': ['uptime', 'availability', 'sla', 'status', 'reliability', 'outage', 'service availability', 'incident']
    },
    {
        'category': 'Products & Services',
        'question': 'What products or services does the company offer?',
        'answer': 'We provide three core products: Nexora Flow (intelligent workflow automation and approval routing), Nexora Cloud Sync (secure enterprise document syncing and access management), and Nexora Insights (real-time business intelligence and reporting dashboards).',
        'keywords': ['product', 'products', 'services', 'offer', 'solutions', 'features', 'flow', 'cloud sync', 'insights', 'what do you sell', 'what do you offer']
    },
    {
        'category': 'Products & Services',
        'question': 'How do I register or create a new Nexora account?',
        'answer': 'You can create an account by clicking the "Sign Up" button on our homepage. Choose your preferred plan, enter your work email, and verify your address. We also offer Single Sign-On (SSO) integration via Google Workspace, Microsoft Azure AD, and Okta.',
        'keywords': ['register', 'registration', 'create account', 'sign up', 'signup', 'open account', 'new user', 'join', 'sso']
    },
    {
        'category': 'Products & Services',
        'question': 'What technical assistance and API integrations are supported?',
        'answer': 'Nexora provides RESTful APIs, webhooks, and pre-built connectors for Slack, Salesforce, Microsoft Teams, and Jira. Developer documentation, SDKs (Python, Node.js, Go), and developer sandbox keys are accessible directly in the developer portal.',
        'keywords': ['technical assistance', 'api', 'integrations', 'developer', 'webhooks', 'rest api', 'sdk', 'connectors', 'jira', 'slack']
    },
    {
        'category': 'Pricing & Payments',
        'question': 'What are your pricing plans and subscription options?',
        'answer': 'We offer three tiers: Starter ($19/user/month billed annually) for growing teams, Professional ($49/user/month) with advanced analytics and integrations, and custom Enterprise licensing tailored for large-scale deployments with dedicated support.',
        'keywords': ['pricing', 'price', 'cost', 'plans', 'subscription', 'rates', 'how much', 'fee', 'tier', 'starter', 'professional', 'enterprise']
    },
    {
        'category': 'Pricing & Payments',
        'question': 'What payment methods do you accept?',
        'answer': 'We accept major credit and debit cards (Visa, MasterCard, American Express, Discover), PayPal, and ACH direct wire transfers for annual contracts. Enterprise clients can also request custom invoiced billing with net-30 payment terms.',
        'keywords': ['payment', 'payment methods', 'credit card', 'pay', 'visa', 'mastercard', 'paypal', 'ach', 'wire transfer', 'invoice', 'billing terms']
    },
    {
        'category': 'Pricing & Payments',
        'question': 'Can I change my billing cycle or update invoice details?',
        'answer': 'Yes, workspace admins can switch between monthly and annual billing cycles, update payment methods, or add VAT/tax identification numbers anytime under Workspace Settings > Billing & Invoices.',
        'keywords': ['billing', 'invoice', 'tax', 'vat', 'billing cycle', 'annual', 'monthly', 'receipt']
    },
    {
        'category': 'Refunds & Cancellations',
        'question': 'What is your refund or cancellation policy?',
        'answer': 'We offer a 14-day hassle-free money-back guarantee on all new monthly and annual subscriptions. If you are not completely satisfied within the first 14 days of purchase, contact our billing team for a prompt full refund without penalties.',
        'keywords': ['refund', 'refund policy', 'cancellation policy', 'money back', 'guarantee', 'cancel', 'return', 'reimbursement']
    },
    {
        'category': 'Refunds & Cancellations',
        'question': 'How do I cancel my subscription or downgrade my plan?',
        'answer': 'To cancel or downgrade, navigate to Workspace Settings > Subscription and select "Cancel Subscription". You will retain full access to all features until the end of your current paid billing period, and no further charges will occur.',
        'keywords': ['cancel subscription', 'downgrade', 'stop plan', 'end subscription', 'terminate', 'cancel account']
    },
    {
        'category': 'Refunds & Cancellations',
        'question': 'What happens to our company data upon cancellation?',
        'answer': 'Following cancellation, your data remains accessible in read-only mode for 30 days so you can export your records in CSV or JSON format. After 30 days, workspace records are permanently purged in compliance with SOC 2 and GDPR protocols.',
        'keywords': ['data retention', 'export data', 'deleted data', 'cancel data', 'gdpr', 'purge', 'privacy']
    },
    {
        'category': 'Customer Support',
        'question': 'How can I contact customer support?',
        'answer': 'You can contact customer support via email at support@nexora-example.com, through in-app live chat during business hours, or by calling our toll-free support line at 1-800-555-0199. Enterprise customers have direct access to their assigned Customer Success Manager.',
        'keywords': ['contact', 'support', 'contact support', 'customer support', 'email', 'phone', 'help desk', 'call', 'reach out', 'ticket']
    },
    {
        'category': 'Customer Support',
        'question': 'How do I reset my password or recover account access?',
        'answer': 'Click "Forgot Password" on the sign-in screen and submit your registered email address. A secure recovery link valid for 60 minutes will be emailed to you immediately. If your organization enforces SSO, please contact your internal IT administrator.',
        'keywords': ['password', 'reset password', 'forgot password', 'recover', 'locked out', 'login issue', 'credentials', 'access']
    },
    {
        'category': 'Customer Support',
        'question': 'Do you offer onboarding assistance and user training?',
        'answer': 'Yes! All plans include access to the Nexora Academy with video walkthroughs and interactive tutorials. Professional and Enterprise tiers include customized live virtual onboarding sessions and training workshops with our solution architects.',
        'keywords': ['onboarding', 'training', 'tutorial', 'academy', 'learn', 'workshops', 'guidance', 'getting started']
    }
]

class Command(BaseCommand):
    help = 'Loads sample Nexora company FAQ records into PostgreSQL and ingests them into vector store.'

    def handle(self, *args, **options):
        ingestion_service = IngestionService()
        created_count = 0
        updated_count = 0

        self.stdout.write("Populating sample FAQs...")
        for item in SAMPLE_FAQS:
            faq, created = FAQ.objects.update_or_create(
                question=item['question'],
                defaults={
                    'answer': item['answer'],
                    'category': item['category'],
                    'keywords': item['keywords'],
                    'is_active': True,
                }
            )
            ingestion_service.ingest_faq(faq)
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {len(SAMPLE_FAQS)} FAQs: "
                f"{created_count} created, {updated_count} updated, and indexed in vector knowledge base."
            )
        )
