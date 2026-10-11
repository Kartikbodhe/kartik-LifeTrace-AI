from datetime import datetime, date, timedelta
from decimal import Decimal
from app import create_app
from extensions import db
from models import User, Memory, Task, PaymentTransaction, Repayment, Promise, Reminder, Notification

def seed_demo_data():
    """Populates rich demonstration data for the demo user."""
    app = create_app("development")
    with app.app_context():
        # Ensure tables exist
        db.create_all()

        user = User.query.filter_by(username="demouser").first()
        if not user:
            user = User(
                username="demouser",
                email="demo@lifetrace.local",
                full_name="Arjun Mehta",
                timezone="Asia/Kolkata",
                currency="₹"
            )
            user.set_password("lifetrace123")
            db.session.add(user)
            db.session.commit()
            print("[Seed] Created user 'demouser' (Password: lifetrace123)")

        # Clear existing records for demo user to prevent duplicates on multiple runs
        Notification.query.filter_by(user_id=user.id).delete()
        Reminder.query.filter_by(user_id=user.id).delete()
        Promise.query.filter_by(user_id=user.id).delete()
        Repayment.query.filter_by(user_id=user.id).delete()
        PaymentTransaction.query.filter_by(user_id=user.id).delete()
        Task.query.filter_by(user_id=user.id).delete()
        Memory.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        today = date.today()
        now = datetime.utcnow()

        # 1. Memories
        memories = [
            Memory(
                user_id=user.id,
                title="Car Insurance Policy & Emergency Contact",
                description="Policy No: POL-2026-98124 with ICICI Lombard. 24x7 Roadside Assistance helpline: 1800-2666. Key coverage includes zero depreciation and engine protect.",
                category="Documents",
                tags="insurance, car, emergency, finance",
                event_date=today + timedelta(days=45),
                status="Active"
            ),
            Memory(
                user_id=user.id,
                title="Semester 6 Major Project Guidelines",
                description="Final viva requires: 1) Spiral-bound report in IEEE format, 2) GitHub repo with test coverage > 80%, 3) Live Docker demo. Guide: Dr. Arvind Swaminathan.",
                category="College",
                tags="college, project, viva, final-year",
                event_date=today + timedelta(days=20),
                status="Active"
            ),
            Memory(
                user_id=user.id,
                title="Apartment Rent Agreement Renewal Details",
                description="11-month lease signed on 1st November. Security deposit receipt stored in document safe. Notice period required is 30 days prior to vacate.",
                category="Personal",
                tags="flat, rent, lease, landlord",
                event_date=today + timedelta(days=90),
                status="Active"
            ),
            Memory(
                user_id=user.id,
                title="Home WiFi Router Configuration & Static IP",
                description="Router Gateway IP: 192.168.1.1. 5GHz network SSID: HyperNet_5G. Static DNS set to Cloudflare 1.1.1.1 and Google 8.8.8.8.",
                category="Work",
                tags="wifi, home, network, credentials",
                event_date=None,
                status="Active"
            )
        ]
        db.session.add_all(memories)

        # 2. Tasks
        tasks = [
            Task(
                user_id=user.id,
                title="Submit Machine Learning Lab Assignment 3",
                description="Implement Logistic Regression from scratch with NumPy and compare accuracy on MNIST dataset.",
                priority="High",
                category="College",
                due_date=now + timedelta(hours=6),
                status="Pending"
            ),
            Task(
                user_id=user.id,
                title="Prepare Q3 Client Performance Presentation",
                description="Consolidate weekly retention analytics, revenue charts, and next sprint milestones into 12 slides.",
                priority="High",
                category="Work",
                due_date=now + timedelta(days=2),
                status="In Progress"
            ),
            Task(
                user_id=user.id,
                title="Renew Vehicle Pollution Under Control (PUC) Certificate",
                description="Visit nearby petrol pump station with RC copy for emissions testing.",
                priority="Medium",
                category="Urgent",
                due_date=now - timedelta(days=1),  # Overdue
                status="Pending"
            ),
            Task(
                user_id=user.id,
                title="Setup Automated Database Backup Cron Script",
                description="Automated sqlite backup script to instance/backups directory daily.",
                priority="Low",
                category="Project",
                due_date=now - timedelta(days=3),
                status="Completed",
                completed_at=now - timedelta(days=1)
            )
        ]
        db.session.add_all(tasks)

        # 3. Payments
        p1 = PaymentTransaction(
            user_id=user.id,
            person_name="Rohan Sharma",
            amount=Decimal("5000.00"),
            transaction_type="LENT",
            transaction_date=today - timedelta(days=14),
            expected_repayment_date=today + timedelta(days=5),
            description="Contributed for Goa trip Airbnb advance booking",
            status="Partially Paid"
        )
        db.session.add(p1)
        db.session.flush()

        r1 = Repayment(
            payment_id=p1.id,
            user_id=user.id,
            amount=Decimal("2000.00"),
            repayment_date=today - timedelta(days=2),
            notes="Paid part 1 via Google Pay"
        )
        db.session.add(r1)

        p2 = PaymentTransaction(
            user_id=user.id,
            person_name="Uncle Rajesh",
            amount=Decimal("10000.00"),
            transaction_type="BORROWED",
            transaction_date=today - timedelta(days=20),
            expected_repayment_date=today + timedelta(days=10),
            description="Emergency laptop motherboard replacement loan",
            status="Partially Paid"
        )
        db.session.add(p2)
        db.session.flush()

        r2 = Repayment(
            payment_id=p2.id,
            user_id=user.id,
            amount=Decimal("5000.00"),
            repayment_date=today - timedelta(days=5),
            notes="First half transferred via IMPS"
        )
        db.session.add(r2)

        p3 = PaymentTransaction(
            user_id=user.id,
            person_name="Priya Patel",
            amount=Decimal("1200.00"),
            transaction_type="LENT",
            transaction_date=today - timedelta(days=30),
            expected_repayment_date=today - timedelta(days=10),
            description="Concert ticket booking",
            status="Settled"
        )
        db.session.add(p3)
        db.session.flush()

        r3 = Repayment(
            payment_id=p3.id,
            user_id=user.id,
            amount=Decimal("1200.00"),
            repayment_date=today - timedelta(days=12),
            notes="Settled in full via UPI"
        )
        db.session.add(r3)

        p4 = PaymentTransaction(
            user_id=user.id,
            person_name="Ankit Mishra",
            amount=Decimal("850.00"),
            transaction_type="BORROWED",
            transaction_date=today - timedelta(days=8),
            expected_repayment_date=today - timedelta(days=2),  # Overdue
            description="Team dinner bill split share",
            status="Pending"
        )
        db.session.add(p4)

        # 4. Promises
        promises = [
            Promise(
                user_id=user.id,
                title="Review Akash's Resume and Give Tech Feedback",
                person_or_org="Akash Verma",
                description="Look over the backend section and recommend adding Docker & SQLAlchemy projects.",
                commitment_date=today - timedelta(days=3),
                follow_up_date=today + timedelta(days=1),
                priority="High",
                status="Pending"
            ),
            Promise(
                user_id=user.id,
                title="Send Machine Learning Study Notes to Classroom Group",
                person_or_org="CS Study Group",
                description="Upload scanned PDF of modules 3 and 4 to Google Drive folder.",
                commitment_date=today - timedelta(days=2),
                follow_up_date=today + timedelta(days=3),
                priority="Medium",
                status="Pending"
            ),
            Promise(
                user_id=user.id,
                title="Submitted Thesis Literature Review Draft",
                person_or_org="Prof. Swaminathan",
                description="Handed in printed copy of chapters 1 & 2 during office hours.",
                commitment_date=today - timedelta(days=10),
                follow_up_date=today - timedelta(days=5),
                priority="High",
                status="Completed",
                completed_at=now - timedelta(days=5)
            )
        ]
        db.session.add_all(promises)

        # 5. Reminders
        reminders = [
            Reminder(
                user_id=user.id,
                title="PUC Certificate Renewal Due",
                description="Emissions certificate expired yesterday. Visit testing station today.",
                due_datetime=now + timedelta(hours=2),
                status="Scheduled",
                related_type="general"
            ),
            Reminder(
                user_id=user.id,
                title="Follow up with Rohan on Remaining ₹3,000",
                description="Expected settlement date is in 5 days.",
                due_datetime=now + timedelta(days=4),
                status="Scheduled",
                related_type="payment"
            )
        ]
        db.session.add_all(reminders)

        # 6. Notifications
        notifications = [
            Notification(
                user_id=user.id,
                title="⚠️ Overdue Alert: Vehicle PUC Certificate",
                message="Your pollution certificate was scheduled for renewal yesterday. Please renew promptly.",
                notification_type="task_due",
                is_read=False,
                created_at=now - timedelta(hours=3)
            ),
            Notification(
                user_id=user.id,
                title="📋 Upcoming Deadline: Machine Learning Lab Assignment 3",
                message="Assignment submission deadline is scheduled for today at 18:00.",
                notification_type="task_due",
                is_read=False,
                created_at=now - timedelta(hours=1)
            ),
            Notification(
                user_id=user.id,
                title="💰 Payment Received: ₹2,000 from Rohan Sharma",
                message="Partial repayment logged for trip advance. Remaining balance: ₹3,000.",
                notification_type="payment_due",
                is_read=True,
                created_at=now - timedelta(days=2)
            )
        ]
        db.session.add_all(notifications)

        db.session.commit()
        print("[Seed] Successfully seeded rich sample data for LifeTrace AI!")

if __name__ == "__main__":
    seed_demo_data()
