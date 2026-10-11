import re
from datetime import datetime, date, timedelta
from dateutil import parser as date_parser

class SmartCaptureService:
    """
    Deterministic Natural Language Parser for LifeTrace AI Smart Capture.
    Extracts intents, entities, amounts, dates, and categories.
    Designed with a clean interface so an LLM provider can be plugged in when configured.
    """

    WEEKDAYS = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    CATEGORIES = {
        "college": ["college", "assignment", "lab", "thesis", "exam", "syllabus", "professor", "class", "campus", "lecture"],
        "work": ["meeting", "client", "boss", "office", "presentation", "report", "sprint", "email", "manager"],
        "project": ["code", "feature", "bug", "deployment", "github", "milestone", "repo", "demo"],
        "finance": ["lent", "borrowed", "fee", "fees", "bill", "salary", "loan", "rent", "repay", "paid", "rupees", "inr"],
        "documents": ["passport", "license", "aadhaar", "pan", "certificate", "id", "insurance", "visa", "renewal"],
        "personal": ["family", "mom", "dad", "friend", "gym", "workout", "birthday", "gift", "party", "call"]
    }

    @classmethod
    def parse(cls, text: str) -> dict:
        """
        Parse raw natural language string into a structured prediction dictionary.
        Never commits to database directly; returns structured preview for user confirmation.
        """
        clean_text = text.strip()
        lower_text = clean_text.lower()

        # Step 1: Detect intent type
        intent = cls._detect_intent(lower_text)
        
        # Step 2: Extract date and time
        extracted_datetime, date_text = cls._extract_date_time(lower_text)

        # Step 3: Extract category
        category = cls._suggest_category(lower_text)

        # Step 4: Extract entity-specific details
        result = {
            "raw_input": clean_text,
            "type": intent,
            "category": category,
            "suggested_date": extracted_datetime.strftime("%Y-%m-%d") if extracted_datetime else None,
            "suggested_datetime": extracted_datetime.strftime("%Y-%m-%d %H:%M") if extracted_datetime else None,
            "date_expression_found": date_text,
            "confidence": 0.85 if date_text else 0.70,
            "engine": "Deterministic Regex & Pattern Engine (AI-Ready Interface)"
        }

        if intent == "payment":
            payment_info = cls._extract_payment_details(clean_text, lower_text)
            result.update(payment_info)
        elif intent == "promise":
            promise_info = cls._extract_promise_details(clean_text, lower_text, date_text)
            result.update(promise_info)
        elif intent == "memory":
            memory_info = cls._extract_memory_details(clean_text, lower_text)
            result.update(memory_info)
        else:
            # Default is task
            task_info = cls._extract_task_details(clean_text, lower_text, date_text)
            result.update(task_info)

        return result

    @classmethod
    def _detect_intent(cls, text: str) -> str:
        # Check payments
        if any(w in text for w in ["lent", "borrowed", "loaned", "lend", "borrow"]) or ("₹" in text or "rs." in text or "rupees" in text):
            if any(w in text for w in ["lent", "borrowed", "lend", "borrow", "give to", "take from"]):
                return "payment"

        # Check promises
        if any(w in text for w in ["promised", "promise", "committed", "commitment", "follow up with", "follow-up"]):
            return "promise"

        # Check memories
        if text.startswith("remember") or text.startswith("note that") or text.startswith("keep in mind") or "memory:" in text:
            return "memory"

        return "task"

    @classmethod
    def _extract_date_time(cls, text: str):
        now = datetime.now()
        target_date = None
        matched_str = None

        # Check "today"
        if "today" in text:
            target_date = now
            matched_str = "today"
        # Check "tomorrow"
        elif "tomorrow" in text:
            target_date = now + timedelta(days=1)
            matched_str = "tomorrow"
        # Check "day after tomorrow"
        elif "day after tomorrow" in text:
            target_date = now + timedelta(days=2)
            matched_str = "day after tomorrow"

        # Check weekdays: "on friday", "this friday", "next monday", etc.
        if not target_date:
            for day_name, day_idx in cls.WEEKDAYS.items():
                pattern = rf"\b(on|this|next|by)?\s*{day_name}\b"
                match = re.search(pattern, text)
                if match:
                    current_idx = now.weekday()
                    days_ahead = (day_idx - current_idx) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    if "next" in match.group(0) and days_ahead < 7:
                        days_ahead += 7
                    target_date = now + timedelta(days=days_ahead)
                    matched_str = match.group(0).strip()
                    break

        # Check "in X days / weeks"
        if not target_date:
            in_match = re.search(r"\bin\s+(\d+)\s+(day|days|week|weeks|month|months)\b", text)
            if in_match:
                qty = int(in_match.group(1))
                unit = in_match.group(2)
                matched_str = in_match.group(0)
                if "day" in unit:
                    target_date = now + timedelta(days=qty)
                elif "week" in unit:
                    target_date = now + timedelta(weeks=qty)
                elif "month" in unit:
                    target_date = now + timedelta(days=qty * 30)

        # Check explicit dates (e.g. 2026-12-25 or 25-12-2026 or Nov 25)
        if not target_date:
            date_match = re.search(r"\b(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)
            if date_match:
                try:
                    target_date = date_parser.parse(date_match.group(1), dayfirst=True)
                    matched_str = date_match.group(0)
                except Exception:
                    pass

        # Extract time if present (e.g. at 5pm, 10:30 am, 4:00)
        hour = 17  # Default 5:00 PM if none specified
        minute = 0
        time_match = re.search(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text)
        if time_match:
            h = int(time_match.group(1))
            m = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3)
            if ampm == "pm" and h < 12:
                h += 12
            elif ampm == "am" and h == 12:
                h = 0
            hour = h
            minute = m

        if target_date:
            target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return target_date, matched_str

        return None, None

    @classmethod
    def _suggest_category(cls, text: str) -> str:
        for cat, keywords in cls.CATEGORIES.items():
            if any(k in text for k in keywords):
                return cat.capitalize()
        return "General"

    @classmethod
    def _extract_payment_details(cls, orig_text: str, lower_text: str) -> dict:
        is_lent = "lent" in lower_text or "lend" in lower_text
        transaction_type = "LENT" if is_lent else "BORROWED"

        # Amount pattern
        amount = "0.00"
        amt_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|rupees)?", lower_text)
        if amt_match:
            amount = amt_match.group(1)

        # Person pattern: "to <Person>" or "from <Person>"
        person = "Someone"
        if is_lent:
            p_match = re.search(r"\bto\s+([A-Za-z]+)", orig_text, re.IGNORECASE)
            if p_match:
                person = p_match.group(1).title()
        else:
            p_match = re.search(r"\bfrom\s+([A-Za-z]+)", orig_text, re.IGNORECASE)
            if p_match:
                person = p_match.group(1).title()

        return {
            "title": f"Payment: ₹{amount} {'lent to' if is_lent else 'borrowed from'} {person}",
            "amount": amount,
            "person_name": person,
            "transaction_type": transaction_type,
            "description": orig_text
        }

    @classmethod
    def _extract_promise_details(cls, orig_text: str, lower_text: str, date_text: str) -> dict:
        person = "Collaborator"
        # Match patterns like: "promised Dr. Sharma to...", "promised to Dr. Sharma that...", "committed with Amit to..."
        p_match = re.search(
            r"\b(?:promised|commit(?:ted)?)\s+(?:to|with)?\s*([A-Za-z\.\s]+?)(?:\s+(?:to|that|about|on|by)|$)",
            orig_text,
            re.IGNORECASE
        )
        if p_match:
            candidate = p_match.group(1).strip().title()
            if candidate and len(candidate) <= 40:
                person = candidate
        else:
            # Fallback to general with/to
            p_match2 = re.search(r"\b(?:with|to)\s+([A-Za-z\.\s]+?)(?:\s+(?:to|that|on|by|about)|$)", orig_text, re.IGNORECASE)
            if p_match2:
                candidate = p_match2.group(1).strip().title()
                if candidate and len(candidate) <= 40:
                    person = candidate

        # Clean title
        title = orig_text
        for prefix in ["i promised", "promised", "i commit to", "committed to", "promise"]:
            if lower_text.startswith(prefix):
                title = orig_text[len(prefix):].strip()
                break

        return {
            "title": title[:100] if title else "Personal Commitment",
            "person_or_org": person,
            "description": orig_text,
            "priority": "Medium"
        }

    @classmethod
    def _extract_memory_details(cls, orig_text: str, lower_text: str) -> dict:
        clean = orig_text
        for prefix in ["remember that", "remember", "note that", "keep in mind", "memory:"]:
            if lower_text.startswith(prefix):
                clean = orig_text[len(prefix):].strip()
                break

        parts = clean.split(".", 1)
        title = parts[0].strip()
        desc = orig_text

        return {
            "title": title[:120] if title else "Saved Memory Note",
            "description": desc,
            "tags": "smart-capture"
        }

    @classmethod
    def _extract_task_details(cls, orig_text: str, lower_text: str, date_text: str) -> dict:
        title = orig_text
        # Strip common lead phrases
        for prefix in ["remind me to", "remind me on friday to", "remind me tomorrow to", "remind me", "please", "i need to", "todo:"]:
            if lower_text.startswith(prefix):
                title = orig_text[len(prefix):].strip()
                break

        # Remove trailing date phrasing from title if clean
        if date_text and date_text.lower() in title.lower():
            # soft clean
            pass

        priority = "High" if any(w in lower_text for w in ["urgent", "asap", "important", "immediately", "today"]) else "Medium"

        return {
            "title": title.capitalize()[:150] if title else "New Task",
            "description": orig_text,
            "priority": priority
        }
