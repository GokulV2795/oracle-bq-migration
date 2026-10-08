from dataclasses import dataclass


@dataclass
class ReconciliationResult:
    source_row_count: int
    extracted_row_count: int
    difference: int
    status: str


def reconcile_counts(
    source_row_count: int,
    extracted_row_count: int
) -> ReconciliationResult:

    difference = source_row_count - extracted_row_count

    if difference == 0:
        status = "MATCH"
    else:
        status = "MISMATCH"

    return ReconciliationResult(
        source_row_count=source_row_count,
        extracted_row_count=extracted_row_count,
        difference=difference,
        status=status,
    )