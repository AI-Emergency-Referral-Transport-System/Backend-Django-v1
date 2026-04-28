from __future__ import annotations

from dataclasses import dataclass

from django.contrib.gis.db.models.functions import Distance

from emergencies.models import HospitalSuggestion
from hospitals.models import Hospital


@dataclass
class HospitalRecommendation:
    hospital: Hospital
    distance_km: float
    score: float
    reason: str


class HospitalSelectionService:
    _TRAUMA_KEYWORDS = {"trauma", "accident", "injury", "bleeding"}
    _CARDIAC_KEYWORDS = {"cardiac", "heart", "stroke", "chest_pain"}
    _MATERNITY_KEYWORDS = {"maternity", "labor", "delivery", "pregnancy"}
    _NEONATAL_KEYWORDS = {"neonatal", "newborn", "infant", "baby"}
    _SURGERY_KEYWORDS = {"surgery", "surgical", "operation"}

    def shortlist(
        self,
        emergency_location,
        emergency_type: str = "",
        priority: str = "",
        limit: int = 5,
    ) -> list[HospitalRecommendation]:
        if emergency_location is None:
            return []

        search_limit = max(limit * 4, 10)
        hospitals = (
            Hospital.objects.filter(is_available=True)
            .exclude(location__isnull=True)
            .annotate(distance=Distance("location", emergency_location))
            .order_by("distance")[:search_limit]
        )

        recommendations: list[HospitalRecommendation] = []
        for hospital in hospitals:
            recommendation = self._build_recommendation(
                hospital=hospital,
                emergency_type=emergency_type,
                priority=priority,
            )
            recommendations.append(recommendation)

        recommendations.sort(key=lambda item: (-item.score, item.distance_km, item.hospital.name))
        return recommendations[:limit]

    def sync_emergency_suggestions(self, emergency, limit: int = 5) -> list[HospitalSuggestion]:
        recommendations = self.shortlist(
            emergency_location=emergency.patient_location,
            emergency_type=emergency.emergency_type,
            priority=emergency.priority,
            limit=limit,
        )

        emergency.hospital_suggestions.all().delete()

        selected_hospital = None
        selected_distance = None
        created_suggestions: list[HospitalSuggestion] = []

        for index, recommendation in enumerate(recommendations):
            suggestion = HospitalSuggestion.objects.create(
                emergency=emergency,
                hospital=recommendation.hospital,
                distance_km=recommendation.distance_km,
                score=recommendation.score,
                reason=recommendation.reason,
                is_selected=index == 0,
            )
            created_suggestions.append(suggestion)

            if index == 0:
                selected_hospital = recommendation.hospital
                selected_distance = recommendation.distance_km

        update_fields: list[str] = []
        if selected_hospital is not None and emergency.selected_hospital_id != selected_hospital.id:
            emergency.selected_hospital = selected_hospital
            update_fields.append("selected_hospital")
        if selected_distance is not None:
            emergency.distance_km = selected_distance
            update_fields.append("distance_km")
        if update_fields:
            emergency.save()

        return created_suggestions

    def mark_selected_hospital(self, emergency, hospital: Hospital) -> HospitalSuggestion:
        emergency.hospital_suggestions.update(is_selected=False)
        suggestion, created = HospitalSuggestion.objects.get_or_create(
            emergency=emergency,
            hospital=hospital,
            defaults={
                "distance_km": self._distance_for_hospital(hospital),
                "score": 0.0,
                "reason": "Selected manually by the patient.",
                "is_selected": True,
            },
        )
        if not created:
            suggestion.is_selected = True
            if not suggestion.reason:
                suggestion.reason = "Selected manually by the patient."
            suggestion.save(update_fields=["is_selected", "reason", "updated_at"])
        return suggestion

    def _build_recommendation(
        self,
        hospital: Hospital,
        emergency_type: str,
        priority: str,
    ) -> HospitalRecommendation:
        normalized_type = (emergency_type or "").strip().lower()
        normalized_priority = (priority or "").strip().lower()
        distance_km = round(getattr(hospital.distance, "km", 0.0), 2)

        reasons: list[str] = []
        score = max(0.0, 60.0 - (distance_km * 2.5))
        reasons.append(f"{distance_km:.2f} km away")

        if hospital.has_emergency:
            score += 10
            reasons.append("has emergency unit")

        if hospital.available_beds > 0:
            score += min(hospital.available_beds, 20)
            reasons.append(f"{hospital.available_beds} bed(s) available")
        else:
            score -= 20
            reasons.append("no available beds")

        if normalized_priority in {"critical", "high"}:
            if hospital.has_icu or hospital.available_icu_beds > 0:
                score += 12
                reasons.append("ICU support available")
            if hospital.oxygen_level in {Hospital.OxygenLevel.HIGH, Hospital.OxygenLevel.MEDIUM}:
                score += 8
                reasons.append(f"oxygen level is {hospital.oxygen_level}")

        if self._matches_keywords(normalized_type, self._TRAUMA_KEYWORDS) and hospital.has_trauma:
            score += 14
            reasons.append("trauma-ready")
        if self._matches_keywords(normalized_type, self._CARDIAC_KEYWORDS) and hospital.has_cardiology:
            score += 14
            reasons.append("cardiology support")
        if self._matches_keywords(normalized_type, self._MATERNITY_KEYWORDS) and hospital.has_maternity:
            score += 14
            reasons.append("maternity support")
        if self._matches_keywords(normalized_type, self._NEONATAL_KEYWORDS) and hospital.has_neonatal:
            score += 14
            reasons.append("neonatal support")
        if self._matches_keywords(normalized_type, self._SURGERY_KEYWORDS) and hospital.has_surgery:
            score += 10
            reasons.append("surgical capability")

        if hospital.verification_status == Hospital.VerificationStatus.APPROVED:
            score += 5
            reasons.append("verified facility")

        return HospitalRecommendation(
            hospital=hospital,
            distance_km=distance_km,
            score=round(score, 2),
            reason=", ".join(reasons),
        )

    def _distance_for_hospital(self, hospital: Hospital) -> float | None:
        distance = getattr(hospital, "distance", None)
        if distance is None:
            return None
        return round(distance.km, 2)

    def _matches_keywords(self, emergency_type: str, keywords: set[str]) -> bool:
        if not emergency_type:
            return False
        return emergency_type in keywords or any(keyword in emergency_type for keyword in keywords)
