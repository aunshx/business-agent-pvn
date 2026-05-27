from app.schemas import Anomaly
from app.services import dataset

_cache: list[Anomaly] = []


def _money(value) -> str:
    value = float(value)
    magnitude = abs(value)
    if magnitude >= 1e9:
        return f"${value / 1e9:.2f}B"
    if magnitude >= 1e6:
        return f"${value / 1e6:.1f}M"
    if magnitude >= 1e3:
        return f"${value / 1e3:.0f}K"
    return f"${value:.0f}"


def _vendor_concentration() -> list[Anomaly]:
    df = dataset.get_dataframe()
    subcat_total = df.groupby("SubCategory")["Amount"].sum()
    vendor_total = df.groupby(["SubCategory", "Vendor"])["Amount"].sum()

    rows = []
    for subcat, total in subcat_total.items():
        if total < 1_000_000:
            continue
        vendors = vendor_total.loc[subcat]
        top_vendor = vendors.idxmax()
        top_amount = vendors.max()
        share = top_amount / total
        if share > 0.5:
            rows.append((subcat, top_vendor, top_amount, total, share))

    rows.sort(key=lambda r: r[4], reverse=True)
    anomalies = []
    for subcat, vendor, top_amount, total, share in rows[:3]:
        severity = "high" if share >= 0.8 else "notable" if share >= 0.65 else "info"
        anomalies.append(Anomaly(
            title=f"{vendor} dominates {subcat}",
            description=f"{vendor} received {share:.0%} of all {subcat} spending ({_money(top_amount)} of {_money(total)}).",
            suggested_question=f"Top 10 vendors in the {subcat} subcategory",
            severity=severity,
        ))
    return anomalies


def _outlier_payments() -> list[Anomaly]:
    df = dataset.get_dataframe()
    stats = df.groupby("Category")["Amount"].agg(["mean", "std"])
    joined = df.join(stats, on="Category")
    threshold = joined["mean"] + 3 * joined["std"]
    outliers = joined[(joined["Amount"] > threshold) & (joined["Amount"] > 10_000_000)].copy()
    outliers["sigma"] = (outliers["Amount"] - outliers["mean"]) / outliers["std"]

    top_per_category = outliers.loc[outliers.groupby("Category")["Amount"].idxmax()]
    top = top_per_category.nlargest(3, "Amount")
    anomalies = []
    for _, row in top.iterrows():
        sigma = row["sigma"]
        severity = "high" if sigma >= 10 else "notable" if sigma >= 6 else "info"
        anomalies.append(Anomaly(
            title=f"Unusually large payment in {row['Category']}",
            description=f"A {_money(row['Amount'])} payment to {row['Vendor']} from {row['Agency']} is {sigma:.1f} standard deviations above the {row['Category']} average.",
            suggested_question=f"Show all payments to {row['Vendor']}",
            severity=severity,
        ))
    return anomalies


def _cross_agency_vendors() -> list[Anomaly]:
    df = dataset.get_dataframe()
    agency_count = df.groupby("Vendor")["Agency"].nunique()
    vendor_total = df.groupby("Vendor")["Amount"].sum()

    qualifying = agency_count[agency_count >= 5]
    top = vendor_total.loc[qualifying.index].nlargest(3)

    anomalies = []
    for vendor, total in top.items():
        count = int(agency_count.loc[vendor])
        severity = "high" if count >= 20 else "notable" if count >= 10 else "info"
        anomalies.append(Anomaly(
            title=f"{vendor} is paid across many agencies",
            description=f"{vendor} received {_money(total)} in total from {count} different agencies.",
            suggested_question=f"Which agencies paid {vendor}?",
            severity=severity,
        ))
    return anomalies


def compute_anomalies() -> list[Anomaly]:
    return _vendor_concentration() + _outlier_payments() + _cross_agency_vendors()


def warm_cache() -> None:
    global _cache
    _cache = compute_anomalies()


def get_anomalies() -> list[Anomaly]:
    return _cache


if __name__ == "__main__":
    for anomaly in compute_anomalies():
        print(f"[{anomaly.severity:8}] {anomaly.title}")
        print(f"           {anomaly.description}")
        print(f"           -> {anomaly.suggested_question}")
