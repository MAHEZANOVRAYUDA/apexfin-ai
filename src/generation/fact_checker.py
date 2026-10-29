"""
Deterministic numerical verbatim fact-checker for ApexFin AI.
Verifies all numbers and financial metrics in generated reports against source evidence.
"""

import re

from src.domain.entities import AnalysisReport, DocumentChunk
from src.domain.exceptions import VerificationFactCheckError


class DeterministicFactChecker:
    """
    Mathematical and verbatim validator that protects against LLM hallucinations.
    Ensures every numerical figure claimed in executive summaries and extracted metrics
    actually exists in the retrieved SEC filings.
    """

    # Identifies numbers, currencies, percentages, and amount multipliers
    NUMBER_PATTERN = re.compile(
        r"[$€£¥]?\s*\(?\d+(?:,\d+)*(?:\.\d+)?%?(?:\s*(?:billion|million|trillion|bps|[bmk]))?\)?",
        re.IGNORECASE,
    )

    @classmethod
    def extract_numbers(cls, text: str) -> list[str]:
        """Extracts and normalizes all numerical candidates from text."""
        matches = [m.group(0) for m in cls.NUMBER_PATTERN.finditer(text)]
        cleaned: list[str] = []
        for m in matches:
            stripped = m.strip("() ,").lower()
            digits_only = re.sub(r"[^\d]", "", stripped)
            # Retain tokens that have at least 2 digits or financial indicators
            if len(digits_only) >= 2 or "%" in stripped or any(c in stripped for c in "$€£¥"):
                cleaned.append(stripped)
        return cleaned

    @classmethod
    def is_number_in_evidence(cls, num_str: str, evidence_corpus: str) -> bool:
        """
        Determines whether a numeric token exists verbatim or in normalized format
        within the combined evidence text.
        """
        evidence_clean = evidence_corpus.lower()
        num_clean = num_str.lower().strip()

        # 1. Direct exact match
        if num_clean in evidence_clean:
            return True

        # 2. Float and integer normalization (handles '383285.0' -> '383,285' or '383285')
        try:
            val_float = float(num_clean.replace("$", "").replace(",", "").replace("%", ""))
            if val_float.is_integer():
                val_int = int(val_float)
                if f"{val_int:,}" in evidence_clean or str(val_int) in evidence_clean:
                    return True
        except ValueError:
            pass

        # 3. Pure digits match (e.g. '$383,285' matching '383,285' in source)
        digits = re.sub(r"[^\d]", "", num_clean)
        if digits and len(digits) >= 2:
            try:
                int_val = int(digits)
                if f"{int_val:,}" in evidence_clean or digits in evidence_clean:
                    return True
            except ValueError:
                pass

        return False

    def verify_report(
        self,
        report: AnalysisReport,
        retrieved_chunks: list[DocumentChunk],
        strict: bool = False,
    ) -> AnalysisReport:
        """
        Scans executive_summary and extracted_metrics against retrieved chunks.
        Adds audit warnings for unverified figures and adjusts confidence score.
        If strict=True, raises VerificationFactCheckError on unverified numbers.
        """
        combined_evidence = " ".join(c.content for c in retrieved_chunks)

        # 1. Collect numbers from executive summary
        summary_numbers = self.extract_numbers(report.executive_summary)

        # 2. Collect numbers from extracted metrics
        metric_numbers: list[str] = []
        for m in report.extracted_metrics:
            val_str = str(m.value)
            metric_numbers.extend(self.extract_numbers(val_str))

        all_target_numbers = list(set(summary_numbers + metric_numbers))

        if not all_target_numbers:
            return report

        verified_count = 0
        unverified_numbers: list[str] = []

        for num in all_target_numbers:
            if self.is_number_in_evidence(num, combined_evidence):
                verified_count += 1
            else:
                unverified_numbers.append(num)

        # Handle unverified numbers
        if unverified_numbers:
            warning_msg = (
                f"[Audit Fact-Check Warning] Unverified numerical figures detected in synthesis: "
                f"{', '.join(unverified_numbers[:5])}. These figures do not match source evidence verbatim."
            )
            report.audit_warnings.append(warning_msg)

            if strict:
                raise VerificationFactCheckError(
                    f"Fact verification failed in strict mode. Unverified figures: {unverified_numbers}"
                )

        # Recalibrate confidence score proportionally to verification ratio
        verification_ratio = verified_count / len(all_target_numbers)
        adjusted_confidence = min(report.confidence_score, verification_ratio)
        report.confidence_score = round(adjusted_confidence, 4)

        return report
