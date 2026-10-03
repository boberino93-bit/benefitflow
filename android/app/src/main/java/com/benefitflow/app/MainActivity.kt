package com.benefitflow.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { BenefitFlowApp() }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BenefitFlowApp() {
    var state by remember { mutableStateOf(DemoState()) }
    val dispatch: (DemoAction) -> Unit = { state = reduce(state, it) }

    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = androidx.compose.ui.graphics.Color(0xFF174D3A),
            secondary = androidx.compose.ui.graphics.Color(0xFF3C6F5D),
            surface = androidx.compose.ui.graphics.Color(0xFFF9FBF8),
            background = androidx.compose.ui.graphics.Color(0xFFF5F7F4)
        )
    ) {
        Scaffold(
            topBar = {
                CenterAlignedTopAppBar(
                    title = { Text("BenefitFlow", fontWeight = FontWeight.Bold) },
                    actions = { AssistChip(onClick = {}, label = { Text("Synthetic demo") }, leadingIcon = { Icon(Icons.Default.Lock, contentDescription = null) }) }
                )
            },
            bottomBar = { BottomNav(state.step, dispatch) }
        ) { padding ->
            when (state.step) {
                DemoStep.HOME -> HomeScreen(state, dispatch, Modifier.padding(padding))
                DemoStep.BENEFITS -> BenefitsScreen(dispatch, Modifier.padding(padding))
                DemoStep.PLAN -> PlanScreen(dispatch, Modifier.padding(padding))
                DemoStep.PROVIDERS -> ProvidersScreen(dispatch, Modifier.padding(padding))
                DemoStep.APPROVAL -> ApprovalScreen(state, dispatch, Modifier.padding(padding))
                DemoStep.RESULT -> ResultScreen(state, dispatch, Modifier.padding(padding))
                DemoStep.ACTIVITY -> ActivityScreen(state, Modifier.padding(padding))
            }
        }
    }
}

@Composable
private fun BottomNav(step: DemoStep, dispatch: (DemoAction) -> Unit) {
    NavigationBar {
        listOf(
            Triple(DemoStep.HOME, Icons.Default.Home, "Home"),
            Triple(DemoStep.BENEFITS, Icons.Default.AccountBalanceWallet, "Benefits"),
            Triple(DemoStep.PROVIDERS, Icons.Default.LocationOn, "Providers"),
            Triple(DemoStep.ACTIVITY, Icons.Default.History, "Activity")
        ).forEach { (target, icon, label) ->
            NavigationBarItem(
                selected = step == target,
                onClick = { dispatch(DemoAction.Navigate(target)) },
                icon = { Icon(icon, contentDescription = label) },
                label = { Text(label) }
            )
        }
    }
}

@Composable
private fun HomeScreen(state: DemoState, dispatch: (DemoAction) -> Unit, modifier: Modifier = Modifier) {
    LazyColumn(modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item {
            Text("Use more of the benefits you already have.", fontSize = 30.sp, fontWeight = FontWeight.ExtraBold, lineHeight = 34.sp)
            Spacer(Modifier.height(8.dp))
            Text("A synthetic proof of concept. No real insurer, provider, claim, payment, or booking action is performed.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                MetricCard("3", "Actionable benefits", Modifier.weight(1f))
                MetricCard("1", "Needs manual review", Modifier.weight(1f))
            }
        }
        item {
            Card(shape = RoundedCornerShape(24.dp)) {
                Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("Proof-of-concept journey", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    ProgressRow("1", "Review plan evidence", true)
                    ProgressRow("2", "Optimize annual spend", state.step.ordinal >= DemoStep.PLAN.ordinal)
                    ProgressRow("3", "Verify a provider", state.selectedProviderId != null)
                    ProgressRow("4", "Approve exact action", state.approved)
                    ProgressRow("5", "Reconcile outcome", state.outcome != BookingOutcome.NOT_STARTED)
                    Button(onClick = { dispatch(DemoAction.Navigate(DemoStep.BENEFITS)) }, modifier = Modifier.fillMaxWidth()) {
                        Text("Start demo")
                    }
                }
            }
        }
        item {
            ElevatedCard {
                Column(Modifier.padding(18.dp)) {
                    Text("Why BenefitFlow?", fontWeight = FontWeight.Bold)
                    Text("Coverage facts stay tied to evidence. Ambiguity stops the flow instead of being guessed. Booking only advances after explicit approval and authoritative confirmation.")
                }
            }
        }
    }
}

@Composable private fun MetricCard(value: String, label: String, modifier: Modifier = Modifier) {
    ElevatedCard(modifier) { Column(Modifier.padding(16.dp)) { Text(value, fontSize = 24.sp, fontWeight = FontWeight.ExtraBold); Text(label, fontSize = 12.sp) } }
}

@Composable private fun ProgressRow(number: String, label: String, done: Boolean) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Surface(shape = RoundedCornerShape(99.dp), color = if (done) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant) {
            Text(if (done) "✓" else number, modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp), color = if (done) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
        }
        Text(label, fontWeight = FontWeight.Medium)
    }
}

@Composable
private fun BenefitsScreen(dispatch: (DemoAction) -> Unit, modifier: Modifier = Modifier) {
    LazyColumn(modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Text("Your benefits", fontSize = 28.sp, fontWeight = FontWeight.ExtraBold); Text("Every number below is synthetic and tied to its source evidence. Low-confidence material ambiguity is blocked from optimization until reviewed.") }
        items(DemoData.benefits) { benefit ->
            ElevatedCard {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(benefit.name, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                        SuggestionChip(onClick = {}, label = { Text(if (benefit.manualReviewRequired) "Manual review" else benefit.confidence) }, leadingIcon = { if (benefit.manualReviewRequired) Icon(Icons.Default.Warning, contentDescription = null) else Icon(Icons.Default.Verified, contentDescription = null) })
                    }
                    Text("${benefit.coveragePercent}% covered · $${benefit.remaining} remaining of $${benefit.annualMaximum}")
                    LinearProgressIndicator(progress = { benefit.remaining.toFloat() / benefit.annualMaximum.toFloat() }, modifier = Modifier.fillMaxWidth())
                    Text("Evidence: ${benefit.evidence}", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    if (benefit.manualReviewRequired) {
                        Text("Blocked from recommendations until the period rule is resolved.", color = MaterialTheme.colorScheme.error, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                    }
                }
            }
        }
        item { Button(onClick = { dispatch(DemoAction.Navigate(DemoStep.PLAN)) }, modifier = Modifier.fillMaxWidth()) { Text("Build utilization plan") } }
    }
}

@Composable
private fun PlanScreen(dispatch: (DemoAction) -> Unit, modifier: Modifier = Modifier) {
    LazyColumn(modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { Text("Recommended plan", fontSize = 28.sp, fontWeight = FontWeight.ExtraBold); Text("Based on a $600 annual out-of-pocket budget.") }
        item { RecommendationCard("Physiotherapy", "6 visits", "$690 provider cost", "$552 insurer", "$138 you", "Highest priority and strong remaining coverage") }
        item { RecommendationCard("Massage therapy", "3 visits", "$390 provider cost", "$312 insurer", "$78 you", "Fits remaining budget after physiotherapy") }
        item { OutlinedCard { Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) { Text("Dental excluded — manual review", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.error); Text("The source wording does not establish the annual-period anchor. BenefitFlow stops this category instead of assuming calendar year or guessing."); Text("Resolve evidence → re-run plan", fontWeight = FontWeight.SemiBold) } } }
        item { Button(onClick = { dispatch(DemoAction.Navigate(DemoStep.PROVIDERS)) }, modifier = Modifier.fillMaxWidth()) { Text("Find a physiotherapist") } }
    }
}

@Composable private fun RecommendationCard(title: String, visits: String, cost: String, insurer: String, user: String, why: String) {
    ElevatedCard { Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) { Text(title, fontSize = 20.sp, fontWeight = FontWeight.Bold); Text("$visits · $cost"); Text("$insurer · $user"); Text(why, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant) } }
}

@Composable
private fun ProvidersScreen(dispatch: (DemoAction) -> Unit, modifier: Modifier = Modifier) {
    LazyColumn(modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Text("Provider evidence", fontSize = 28.sp, fontWeight = FontWeight.ExtraBold); Text("Identity, direct billing, price, and availability are separate assertions with separate freshness. A fresh availability signal does not make an older direct-billing claim fresh.") }
        items(DemoData.providers) { provider ->
            ElevatedCard {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(provider.name, fontWeight = FontWeight.Bold, fontSize = 19.sp)
                    Text("${provider.specialty} · $${provider.price} demo price")
                    Text("Direct billing: ${provider.directBilling}")
                    Text("Availability: ${provider.availability}")
                    Text(provider.evidenceAge, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    if (provider.directBilling == "Unknown") {
                        AssistChip(onClick = {}, label = { Text("Direct billing requires verification") }, leadingIcon = { Icon(Icons.Default.Warning, contentDescription = null) })
                    }
                    Button(onClick = { dispatch(DemoAction.SelectProvider(provider.id)) }, modifier = Modifier.fillMaxWidth()) { Text("Review exact booking proposal") }
                }
            }
        }
    }
}

@Composable
private fun ApprovalScreen(state: DemoState, dispatch: (DemoAction) -> Unit, modifier: Modifier = Modifier) {
    val provider = DemoData.providers.firstOrNull { it.id == state.selectedProviderId }
    LazyColumn(modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { Text("Approve the exact action", fontSize = 28.sp, fontWeight = FontWeight.ExtraBold); Text("Approval is scoped and final for this proposal. It does not authorize a materially different provider, price, time, claim, or payment. Material changes require a new proposal and fresh approval.") }
        item {
            ElevatedCard {
                Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    Text(provider?.name ?: "No provider selected", fontWeight = FontWeight.Bold, fontSize = 20.sp)
                    Text("Physiotherapy · ${provider?.availability ?: "—"}")
                    Text("Expected demo price: $${provider?.price ?: 0}")
                    Text("Estimated insurer contribution: $92")
                    Text("Estimated you pay: $23")
                    HorizontalDivider()
                    Text("Permitted disclosure", fontWeight = FontWeight.Bold)
                    Text("Name · plan number · member/certificate ID — only if reconfirmed necessary for this exact provider workflow.")
                    Text("Not authorized: payment, claim submission, unrelated health information, or a different appointment.", color = MaterialTheme.colorScheme.error)
                    AssistChip(onClick = {}, label = { Text("Demo authorization · expires with this proposal") }, leadingIcon = { Icon(Icons.Default.Lock, contentDescription = null) })
                }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(onClick = { dispatch(DemoAction.Approve) }, enabled = !state.approved, modifier = Modifier.weight(1f)) { Text(if (state.approved) "Approved" else "Approve") }
                OutlinedButton(onClick = { dispatch(DemoAction.Decline) }, enabled = !state.approved, modifier = Modifier.weight(1f)) { Text("Decline") }
            }
        }
        if (state.approved) {
            item { Text("Choose a synthetic transaction outcome", fontWeight = FontWeight.Bold) }
            item { ScenarioButtons(dispatch) }
        }
    }
}

@Composable private fun ScenarioButtons(dispatch: (DemoAction) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Button(onClick = { dispatch(DemoAction.Simulate(BookingOutcome.CONFIRMED_BOOKED)) }, modifier = Modifier.fillMaxWidth()) { Text("Simulate confirmed booking") }
        OutlinedButton(onClick = { dispatch(DemoAction.Simulate(BookingOutcome.WAITLISTED)) }, modifier = Modifier.fillMaxWidth()) { Text("Simulate waitlist") }
        OutlinedButton(onClick = { dispatch(DemoAction.Simulate(BookingOutcome.RECONCILIATION_REQUIRED)) }, modifier = Modifier.fillMaxWidth()) { Text("Simulate ambiguous post-send outcome") }
        OutlinedButton(onClick = { dispatch(DemoAction.Simulate(BookingOutcome.RETRYABLE_FAILURE)) }, modifier = Modifier.fillMaxWidth()) { Text("Simulate safe retryable failure") }
        OutlinedButton(onClick = { dispatch(DemoAction.Simulate(BookingOutcome.REJECTED)) }, modifier = Modifier.fillMaxWidth()) { Text("Simulate provider rejection") }
    }
}

@Composable
private fun ResultScreen(state: DemoState, dispatch: (DemoAction) -> Unit, modifier: Modifier = Modifier) {
    val (title, detail) = when (state.outcome) {
        BookingOutcome.CONFIRMED_BOOKED -> "Appointment confirmed" to "Authoritative provider confirmation exists. A demo calendar projection may now be created."
        BookingOutcome.WAITLISTED -> "Waitlisted — not booked" to "No appointment is counted as confirmed."
        BookingOutcome.RETRYABLE_FAILURE -> "Safe retry possible" to "The failure occurred before any business action could have reached the provider."
        BookingOutcome.RECONCILIATION_REQUIRED -> "Reconciliation required" to "The request may have reached the provider. BenefitFlow must check before retrying."
        BookingOutcome.REJECTED -> "No booking" to "The provider or user declined the transaction."
        BookingOutcome.NOT_STARTED -> "No outcome yet" to "Run a synthetic transaction from the approval screen."
    }
    LazyColumn(modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item {
            AssistChip(onClick = {}, label = { Text(if (state.outcome == BookingOutcome.CONFIRMED_BOOKED) "Confirmed by provider" else "Not a confirmed booking") }, leadingIcon = { Icon(if (state.outcome == BookingOutcome.CONFIRMED_BOOKED) Icons.Default.Verified else Icons.Default.Info, contentDescription = null) })
            Spacer(Modifier.height(12.dp))
            Text(title, fontSize = 30.sp, fontWeight = FontWeight.ExtraBold); Text(detail)
        }
        item { ElevatedCard { Column(Modifier.padding(20.dp)) { Text("Transaction truth", fontWeight = FontWeight.Bold); Text("Only CONFIRMED_BOOKED is treated as a confirmed appointment. Calendar state, transport success, waitlists, or call completion never substitute for provider confirmation.") } } }
        item { Button(onClick = { dispatch(DemoAction.Navigate(DemoStep.ACTIVITY)) }, modifier = Modifier.fillMaxWidth()) { Text("View audit trail") } }
        item { OutlinedButton(onClick = { dispatch(DemoAction.Reset) }, modifier = Modifier.fillMaxWidth()) { Text("Restart demo") } }
    }
}

@Composable
private fun ActivityScreen(state: DemoState, modifier: Modifier = Modifier) {
    LazyColumn(modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item { Text("Activity & audit", fontSize = 28.sp, fontWeight = FontWeight.ExtraBold); Text("Sanitized demo events. No raw member or plan identifiers are stored here. GitHub/AgentBus remains the project source of truth; this screen is user-facing audit context only.") }
        items(state.activity.reversed()) { event -> ListItem(headlineContent = { Text(event) }, leadingContent = { Icon(Icons.Default.CheckCircle, contentDescription = null) }) }
    }
}
