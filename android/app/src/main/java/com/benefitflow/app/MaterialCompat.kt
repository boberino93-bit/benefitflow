package com.benefitflow.app

import androidx.compose.runtime.Composable

/**
 * Compatibility wrapper for Material3 SuggestionChip.
 * Material3 exposes the leading slot as `icon`; the app call site uses
 * `leadingIcon` consistently with AssistChip.
 */
@Composable
fun SuggestionChip(
    onClick: () -> Unit,
    label: @Composable () -> Unit,
    leadingIcon: @Composable (() -> Unit)? = null,
) {
    androidx.compose.material3.SuggestionChip(
        onClick = onClick,
        label = label,
        icon = leadingIcon,
    )
}
