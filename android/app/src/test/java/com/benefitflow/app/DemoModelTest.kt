package com.benefitflow.app

import org.junit.Assert.*
import org.junit.Test

class DemoModelTest {
    @Test fun approvalRequiresSelectedProvider() {
        val next = reduce(DemoState(), DemoAction.Approve)
        assertFalse(next.approved)
    }

    @Test fun confirmationRequiresApproval() {
        val selected = reduce(DemoState(), DemoAction.SelectProvider("physio-1"))
        val blocked = reduce(selected, DemoAction.Simulate(BookingOutcome.CONFIRMED_BOOKED))
        assertEquals(BookingOutcome.NOT_STARTED, blocked.outcome)
    }

    @Test fun approvedFlowCanConfirm() {
        val selected = reduce(DemoState(), DemoAction.SelectProvider("physio-1"))
        val approved = reduce(selected, DemoAction.Approve)
        val confirmed = reduce(approved, DemoAction.Simulate(BookingOutcome.CONFIRMED_BOOKED))
        assertEquals(BookingOutcome.CONFIRMED_BOOKED, confirmed.outcome)
        assertEquals(DemoStep.RESULT, confirmed.step)
    }

    @Test fun ambiguousOutcomeNeverCountsAsConfirmed() {
        val selected = reduce(DemoState(), DemoAction.SelectProvider("physio-1"))
        val approved = reduce(selected, DemoAction.Approve)
        val result = reduce(approved, DemoAction.Simulate(BookingOutcome.RECONCILIATION_REQUIRED))
        assertNotEquals(BookingOutcome.CONFIRMED_BOOKED, result.outcome)
    }

    @Test fun approvalCannotBeReversed() {
        val selected = reduce(DemoState(), DemoAction.SelectProvider("physio-1"))
        val approved = reduce(selected, DemoAction.Approve)
        val declinedAfterApproval = reduce(approved, DemoAction.Decline)
        assertTrue(declinedAfterApproval.approved)
        assertEquals(BookingOutcome.NOT_STARTED, declinedAfterApproval.outcome)
    }

    @Test fun transactionOutcomeIsIdempotent() {
        val selected = reduce(DemoState(), DemoAction.SelectProvider("physio-1"))
        val approved = reduce(selected, DemoAction.Approve)
        val first = reduce(approved, DemoAction.Simulate(BookingOutcome.WAITLISTED))
        val second = reduce(first, DemoAction.Simulate(BookingOutcome.CONFIRMED_BOOKED))
        assertEquals(BookingOutcome.WAITLISTED, second.outcome)
    }
}
