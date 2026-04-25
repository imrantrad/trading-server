"""Legal & Regulatory Infrastructure - ToS, Privacy, Risk Disclosure, KYC"""
import json, sqlite3, os, hashlib
from datetime import datetime
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../database/legal.db")

class LegalModule:
    def __init__(self):
        self._init_db()

    def _conn(self):
        c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS user_consents(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT, consent_type TEXT,
                version TEXT, accepted INTEGER DEFAULT 0,
                ip TEXT DEFAULT '', digital_signature TEXT,
                timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS kyc_submissions(
                id TEXT PRIMARY KEY, user_id TEXT,
                status TEXT DEFAULT 'PENDING',
                pan_hash TEXT DEFAULT '', aadhaar_hash TEXT DEFAULT '',
                selfie_verified INTEGER DEFAULT 0,
                submitted_at TEXT, verified_at TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            );
            """)

    LEGAL_DOCS = {
        "tos": {
            "version": "1.0",
            "title": "Terms of Service",
            "sections": [
                {"heading": "1. Tool Disclaimer", "content": "TRD v12.3 is a financial analytics tool only. We are NOT a SEBI-registered investment advisor. All trading decisions are solely yours. Past performance does not guarantee future results."},
                {"heading": "2. No Liability", "content": "The Company shall not be liable for any trading losses, system outages, data errors, or missed signals. By using this platform, you accept full responsibility for your trading decisions."},
                {"heading": "3. Derivatives Risk", "content": "Options and futures trading carries substantial risk of loss. You may lose more than your initial investment. Only trade with capital you can afford to lose."},
                {"heading": "4. Subscription Terms", "content": "Subscriptions auto-renew monthly unless cancelled. Refunds are available within 3 days of purchase if no AI signals were accessed."},
                {"heading": "5. Data Usage", "content": "We collect trading data to improve AI models. Your personal data is never sold to third parties. See Privacy Policy for details."},
                {"heading": "6. Prohibited Use", "content": "Market manipulation, unauthorized API access, sharing credentials, or using AI signals for front-running are strictly prohibited and may result in account termination."},
            ],
        },
        "privacy": {
            "version": "1.0",
            "title": "Privacy Policy (GDPR & DPDP Act Compliant)",
            "sections": [
                {"heading": "Data We Collect", "content": "Username, email, trading preferences, strategy configurations, and anonymized trade data for AI model training."},
                {"heading": "How We Use Data", "content": "To provide personalized AI signals, improve model accuracy, process payments, and send account notifications."},
                {"heading": "Data Storage", "content": "All data encrypted at rest (AES-256) and in transit (TLS 1.3). Stored in AWS Stockholm region with SOC2 compliance."},
                {"heading": "Your Rights (DPDP 2023)", "content": "Right to access, correct, port, and erase your data. Submit requests to privacy@trd.app. Processed within 72 hours."},
                {"heading": "Data Retention", "content": "Trade data retained 7 years per SEBI regulations. Account data deleted within 30 days of account closure upon request."},
            ],
        },
        "risk_disclosure": {
            "version": "1.0",
            "title": "Derivative Trading Risk Disclosure",
            "warnings": [
                "⚠️ Derivatives trading is HIGHLY SPECULATIVE and carries UNLIMITED LOSS POTENTIAL for futures.",
                "⚠️ Options can expire WORTHLESS, resulting in 100% loss of premium paid.",
                "⚠️ Leverage amplifies BOTH profits AND losses. A 1% market move can mean 10-50% loss of margin.",
                "⚠️ AI signals are NOT guarantees. All signals have failure probability.",
                "⚠️ Past win rates do NOT predict future performance.",
                "⚠️ Algorithmic trading can malfunction. Always monitor positions manually.",
                "⚠️ This platform is NOT a SEBI-registered investment advisor.",
            ],
            "acknowledgments": [
                "I understand I may lose my entire investment",
                "I am trading with capital I can afford to lose",
                "I have read and understood the risk warnings above",
                "I acknowledge TRD is a tool, not an advisor",
                "I accept full responsibility for my trading decisions",
            ],
        },
        "kyc_info": {
            "title": "KYC Verification (Layout - Pending Implementation)",
            "status": "LAYOUT_ONLY",
            "required_docs": ["PAN Card", "Aadhaar Card", "Selfie with PAN", "Bank Statement"],
            "note": "Full KYC implementation will be added as specified. Current: Layout only.",
        },
    }

    def get_doc(self, doc_type: str) -> dict:
        return self.LEGAL_DOCS.get(doc_type, {})

    def record_consent(self, user_id, consent_type, version, ip="") -> dict:
        sig = hashlib.sha256(f"{user_id}|{consent_type}|{version}|{datetime.now().isoformat()}".encode()).hexdigest()
        with self._conn() as c:
            c.execute("INSERT INTO user_consents(user_id,consent_type,version,accepted,ip,digital_signature,timestamp) VALUES(?,?,?,1,?,?,?)",
                (user_id,consent_type,version,ip,sig,datetime.now().isoformat()))
        return {"consent_recorded":True,"digital_signature":sig,"timestamp":datetime.now().isoformat()}

    def get_consents(self, user_id) -> list:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM user_consents WHERE user_id=? AND accepted=1", (user_id,)).fetchall()
        return [dict(r) for r in rows]

    def has_signed_risk_disclosure(self, user_id) -> bool:
        with self._conn() as c:
            row = c.execute("SELECT id FROM user_consents WHERE user_id=? AND consent_type='risk_disclosure' AND accepted=1", (user_id,)).fetchone()
        return row is not None

legal = LegalModule()
