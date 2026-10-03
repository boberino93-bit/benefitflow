package com.benefitflow.app

enum class DemoStep { HOME, BENEFITS, PLAN, PROVIDERS, APPROVAL, RESULT, ACTIVITY }
enum class BookingOutcome { NOT_STARTED, CONFIRMED_BOOKED, WAITLISTED, RETRYABLE_FAILURE, RECONCILIATION_REQUIRED, REJECTED }

data class BenefitItem(
    val name: String,
    val coveragePercent: Int,
    val annualMaximum: Int,
    val remaining: Int,
    val evidence: String,
    val confidence: String = "High",
    val manualReviewRequired: Boolean = false
)

data class ProviderItem(
    val id: String,
    val name: String,
    val specialty: String,
    val price: Int,
    val directBilling: String,
    val availability: String,
    val evidenceAge: String
)

data class DemoState(
    val step: DemoStep = DemoStep.HOME,
    val selectedProviderId: String? = null,
    val approved: Boolean = false,
    val outcome: BookingOutcome = BookingOutcome.NOT_STARTED,
    val activity: List<String> = listOf("Demo ready — no external actions authorized")
)

sealed interface DemoAction {
    data class Navigate(val step: DemoStep) : DemoAction
    data class SelectProvider(val providerId: String) : DemoAction
    data object Approve : DemoAction
    data object Decline : DemoAction
    data class Simulate(val outcome: BookingOutcome) : DemoAction
    data object Reset : DemoAction
}

object DemoData {
    val benefits = listOf(
        BenefitItem("Physiotherapy", 80, 1000, 650, "Plan text · annual maximum · calendar year"),
        BenefitItem("Massage therapy", 80, 750, 500, "Plan text · annual maximum · calendar year"),
        BenefitItem("Psychology", 80, 1500, 1150, "Plan text · annual maximum · calendar year"),
        BenefitItem("Dental", 80, 1200, 900, "Plan text · period anchor unclear", confidence = "Low", manualReviewRequired = true)
    )
    val providers = listOf(
        ProviderItem("physio-1", "Harbour Demo Physiotherapy", "Physiotherapy", 115, "Confirmed", "Tue 3:00 PM", "Verified 4 min ago"),
        ProviderItem("physio-2", "Northstar Demo Rehab", "Physiotherapy", 105, "Unknown", "Wed 10:30 AM", "Verified 18 min ago")
    )
}

fun reduce(state: DemoState, action: DemoAction): DemoState = when (action) {
    is DemoAction.Navigate -> state.copy(step = action.step)
    is DemoAction.SelectProvider -> state.copy(
        selectedProviderId = action.providerId,
        step = DemoStep.APPROVAL,
        activity = state.activity + "Provider selected: ${action.providerId}"
    )
    DemoAction.Approve -> if (state.selectedProviderId == null || state.approved || state.outcome != BookingOutcome.NOT_STARTED) state else state.copy(
        approved = true,
        activity = state.activity + "Exact demo transaction approved — authorization is final for this proposal"
    )
    DemoAction.Decline -> if (state.approved || state.outcome != BookingOutcome.NOT_STARTED) state else state.copy(
        approved = false,
        outcome = BookingOutcome.REJECTED,
        step = DemoStep.RESULT,
        activity = state.activity + "Transaction declined — no external action authorized"
    )
    is DemoAction.Simulate -> if (!state.approved || state.outcome != BookingOutcome.NOT_STARTED) state else state.copy(
        outcome = action.outcome,
        step = DemoStep.RESULT,
        activity = state.activity + when (action.outcome) {
            BookingOutcome.CONFIRMED_BOOKED -> "Simulated provider confirmation received"
            BookingOutcome.WAITLISTED -> "Simulated waitlist response — not booked"
            BookingOutcome.RETRYABLE_FAILURE -> "Simulated pre-send failure — safe retry possible"
            BookingOutcome.RECONCILIATION_REQUIRED -> "Ambiguous post-send outcome — reconciliation required"
            BookingOutcome.REJECTED -> "Simulated provider rejection"
            BookingOutcome.NOT_STARTED -> "Simulation not started"
        }
    )
    DemoAction.Reset -> DemoState()
}
