import logging

import pandas as pd
from tabulate import tabulate

logger = logging.getLogger(name=__name__)


def log_municipality_update(original: pd.Series, updated: pd.Series) -> None:
    """Log how many codes were updated and show distribution table."""
    changes_mask = original.ne(updated)
    updated_count = changes_mask.sum()
    logger.info(f"{updated_count} municipality codes were updated.")

    if updated_count == 0:
        return

    update_distr = (
        pd.DataFrame(
            {
                "from": original[changes_mask],
                "to": updated[changes_mask],
            }
        )
        .value_counts()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    table_str = tabulate(
        update_distr.to_records(index=False),
        headers="keys",
        tablefmt="pretty",
        showindex=False,
    )

    logger.info("Distribution of municipality code updates:\n" + table_str)
