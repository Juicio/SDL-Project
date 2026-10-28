"""Neighborhood archetype clustering for the Omaha-Council Bluffs SLD project.

Run from the repository root:
    python adithya/neighborhood_clustering.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kruskal
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler


SEED = 8320
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "EPA_SDL_OmahaCouncilBluffs.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "results"

FEATURE_LABELS = {
    "log_population_density": "Population density (log)",
    "log_employment_density": "Employment density (log)",
    "land_use_mix": "Land-use mix",
    "log_intersection_density": "Intersection density (log)",
    "transit_access_rank": "Transit-access rank",
    "auto_job_accessibility": "Auto job accessibility",
}

# Names were assigned after examining each cluster's standardized profile.
ARCHETYPE_NAMES = {
    0: "Transit-Poor Mixed-Use Areas",
    1: "Transit-Served Residential Areas",
    2: "Low-Density Peripheral Areas",
    3: "Auto-Oriented Residential Areas",
    4: "Transit-Accessible Mixed-Use Centers",
}


def build_features(data: pd.DataFrame) -> pd.DataFrame:
    """Construct interpretable, non-duplicative clustering features."""
    return pd.DataFrame(
        {
            "log_population_density": np.log1p(data["D1B"]),
            "log_employment_density": np.log1p(data["D1C"]),
            "land_use_mix": data["D2A_EPHHM"],
            "log_intersection_density": np.log1p(data["D3B"]),
            # EPA assigns 1 to block groups without transit and 13-20 to
            # served block groups. This avoids treating -99999 as distance.
            "transit_access_rank": data["D4A_Ranked"],
            "auto_job_accessibility": data["D5CRI"],
        }
    )


def save_model_selection(z: np.ndarray) -> pd.DataFrame:
    rows = []
    for k in range(2, 9):
        model = KMeans(n_clusters=k, n_init=100, random_state=SEED)
        labels = model.fit_predict(z)
        rows.append(
            {
                "k": k,
                "within_cluster_sum_of_squares": model.inertia_,
                "silhouette_score": silhouette_score(z, labels),
            }
        )

    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUTPUT_DIR / "model_selection.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    axes[0].plot(metrics["k"], metrics["within_cluster_sum_of_squares"], marker="o")
    axes[0].axvline(5, color="#C44E52", linestyle="--", linewidth=1)
    axes[0].set(title="Elbow method", xlabel="Number of clusters (k)", ylabel="Within-cluster sum of squares")
    axes[1].plot(metrics["k"], metrics["silhouette_score"], marker="o")
    axes[1].axvline(5, color="#C44E52", linestyle="--", linewidth=1)
    axes[1].set(title="Silhouette comparison", xlabel="Number of clusters (k)", ylabel="Average silhouette score")
    fig.suptitle("Choosing the number of neighborhood archetypes")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "model_selection.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return metrics


def run_robustness_checks(data, features, z, reference_labels):
    """Test initialization, subsample, algorithm, and feature sensitivity."""
    seed_rows = []
    for seed in range(50):
        labels = KMeans(n_clusters=5, n_init=20, random_state=seed).fit_predict(z)
        seed_rows.append({
            "Check": "Random initialization", "Run": seed + 1,
            "Adjusted_Rand_Index": adjusted_rand_score(reference_labels, labels),
        })

    rng = np.random.default_rng(SEED)
    subsample_rows = []
    for run in range(100):
        sample_index = rng.choice(len(z), size=int(0.80 * len(z)), replace=False)
        fitted = KMeans(n_clusters=5, n_init=30, random_state=run).fit(z[sample_index])
        subsample_rows.append({
            "Check": "80% subsample", "Run": run + 1,
            "Adjusted_Rand_Index": adjusted_rand_score(reference_labels, fitted.predict(z)),
        })
    stability = pd.DataFrame(seed_rows + subsample_rows)
    stability.to_csv(OUTPUT_DIR / "stability_runs.csv", index=False)

    hierarchy_labels = AgglomerativeClustering(n_clusters=5, linkage="ward").fit_predict(z)
    comparisons = [{
        "Analysis": "Base K-means", "Feature_count": 6,
        "Silhouette_score": silhouette_score(z, reference_labels), "ARI_vs_base": 1.0,
    }, {
        "Analysis": "Ward hierarchical clustering", "Feature_count": 6,
        "Silhouette_score": silhouette_score(z, hierarchy_labels),
        "ARI_vs_base": adjusted_rand_score(reference_labels, hierarchy_labels),
    }]

    expanded = features.assign(
        employment_mix=data["D2B_E8MIXA"], walkability=data["NatWalkInd"]
    )
    alternatives = {
        "Remove population density": ["log_employment_density", "land_use_mix",
            "log_intersection_density", "transit_access_rank", "auto_job_accessibility"],
        "Remove intersection density": ["log_population_density", "log_employment_density",
            "land_use_mix", "transit_access_rank", "auto_job_accessibility"],
        "Add employment-mix entropy": [*features.columns, "employment_mix"],
        "Remove auto job accessibility": ["log_population_density", "log_employment_density",
            "land_use_mix", "log_intersection_density", "transit_access_rank"],
        "Compact walkability specification": ["log_population_density",
            "log_employment_density", "walkability", "auto_job_accessibility"],
    }
    for name, columns in alternatives.items():
        alternative_z = StandardScaler().fit_transform(expanded[columns])
        labels = KMeans(n_clusters=5, n_init=100, random_state=SEED).fit_predict(alternative_z)
        comparisons.append({
            "Analysis": name, "Feature_count": len(columns),
            "Silhouette_score": silhouette_score(alternative_z, labels),
            "ARI_vs_base": adjusted_rand_score(reference_labels, labels),
        })
    comparisons = pd.DataFrame(comparisons)
    comparisons.to_csv(OUTPUT_DIR / "robustness_comparisons.csv", index=False)

    scores = silhouette_samples(z, reference_labels)
    score_data = pd.DataFrame({
        "Cluster": reference_labels + 1,
        "Archetype": pd.Series(reference_labels).map(ARCHETYPE_NAMES),
        "Silhouette": scores,
    })
    cluster_summary = score_data.groupby(["Cluster", "Archetype"], as_index=False).agg(
        Block_groups=("Silhouette", "size"),
        Mean_silhouette=("Silhouette", "mean"),
        Median_silhouette=("Silhouette", "median"),
        Negative_silhouette_share=("Silhouette", lambda values: (values < 0).mean()),
    )
    cluster_summary.to_csv(OUTPUT_DIR / "cluster_silhouette_summary.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    subsample_values = stability.loc[stability["Check"] == "80% subsample",
                                     "Adjusted_Rand_Index"]
    axes[0].hist(subsample_values, bins=12, color="#4C72B0", edgecolor="white")
    axes[0].axvline(subsample_values.median(), color="#C44E52", linestyle="--")
    axes[0].set(title="Stability across 100 subsamples",
                xlabel="Adjusted Rand Index versus full-data solution",
                ylabel="Number of runs")
    axes[1].barh(cluster_summary["Archetype"], cluster_summary["Mean_silhouette"],
                 color="#55A868")
    axes[1].axvline(0, color="black", linewidth=0.8)
    axes[1].set(title="Separation quality by archetype", xlabel="Mean silhouette score")
    fig.suptitle("Robustness checks for the five-cluster solution")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "robustness_validation.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return stability, comparisons, cluster_summary


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(DATA_PATH, dtype={"GEOID10": str, "GEOID20": str})

    if data.shape[0] != 727:
        raise ValueError(f"Expected 727 block groups, found {data.shape[0]}.")

    # The county-subset CSV was exported with its original GEOID fields
    # rounded to county-level values. Reconstruct the 12-digit census block-
    # group identifier from the component fields so map joins remain valid.
    data["GEOID"] = (
        data["STATEFP"].astype(int).astype(str).str.zfill(2)
        + data["COUNTYFP"].astype(int).astype(str).str.zfill(3)
        + data["TRACTCE"].astype(int).astype(str).str.zfill(6)
        + data["BLKGRPCE"].astype(int).astype(str).str.zfill(1)
    )
    if data["GEOID"].nunique() != data.shape[0]:
        raise ValueError("Reconstructed census block-group GEOIDs are not unique.")

    features = build_features(data)
    if not np.isfinite(features.to_numpy()).all():
        raise ValueError("Clustering features contain missing or non-finite values.")

    scaler = StandardScaler()
    z = scaler.fit_transform(features)
    save_model_selection(z)

    model = KMeans(n_clusters=5, n_init=100, random_state=SEED)
    raw_cluster = model.fit_predict(z)
    archetype = pd.Series(raw_cluster).map(ARCHETYPE_NAMES)
    stability, robustness, cluster_silhouette = run_robustness_checks(
        data, features, z, raw_cluster
    )

    assignments = data.copy()
    assignments.insert(0, "Archetype", archetype)
    assignments.insert(0, "Cluster", raw_cluster + 1)
    assignments["State"] = assignments["STATEFP"].map({31: "Nebraska", 19: "Iowa"})
    assignments["County"] = assignments.apply(
        lambda row: {
            (31, 55): "Douglas",
            (31, 153): "Sarpy",
            (19, 155): "Pottawattamie",
        }.get((row["STATEFP"], row["COUNTYFP"]), "Other"),
        axis=1,
    )
    assignments.to_csv(OUTPUT_DIR / "cluster_assignments.csv", index=False)

    profile_input = pd.DataFrame(
        {
            "Cluster": raw_cluster + 1,
            "Archetype": archetype,
            "Population density (people/acre)": data["D1B"],
            "Employment density (jobs/acre)": data["D1C"],
            "Land-use mix (0-1)": data["D2A_EPHHM"],
            "Intersection density": data["D3B"],
            "Transit-access rank": data["D4A_Ranked"],
            "Auto job accessibility (0-1)": data["D5CRI"],
            "National Walkability Index": data["NatWalkInd"],
            "Zero-car household share": data["Pct_AO0"],
        }
    )
    profiles = (
        profile_input.groupby(["Cluster", "Archetype"], as_index=False)
        .agg(
            Block_groups=("Zero-car household share", "size"),
            Population_density=("Population density (people/acre)", "mean"),
            Employment_density=("Employment density (jobs/acre)", "mean"),
            Land_use_mix=("Land-use mix (0-1)", "mean"),
            Intersection_density=("Intersection density", "mean"),
            Transit_access_rank=("Transit-access rank", "mean"),
            Auto_job_accessibility=("Auto job accessibility (0-1)", "mean"),
            Walkability_index=("National Walkability Index", "mean"),
            Zero_car_household_share=("Zero-car household share", "mean"),
        )
        .sort_values("Cluster")
    )
    profiles.to_csv(OUTPUT_DIR / "cluster_profiles.csv", index=False)

    state_composition = pd.crosstab(
        index=[assignments["Cluster"], assignments["Archetype"]],
        columns=assignments["State"],
        margins=True,
    ).reset_index()
    state_composition.to_csv(OUTPUT_DIR / "state_cluster_composition.csv", index=False)

    z_profiles = pd.DataFrame(z, columns=FEATURE_LABELS.keys())
    z_profiles["Archetype"] = archetype
    z_means = z_profiles.groupby("Archetype").mean().loc[list(ARCHETYPE_NAMES.values())]
    fig, ax = plt.subplots(figsize=(11, 5.2))
    image = ax.imshow(z_means, cmap="RdBu_r", vmin=-2.5, vmax=2.5, aspect="auto")
    ax.set_xticks(range(len(FEATURE_LABELS)))
    ax.set_xticklabels(FEATURE_LABELS.values(), rotation=30, ha="right")
    ax.set_yticks(range(len(z_means)))
    ax.set_yticklabels(z_means.index)
    ax.set_title("Standardized profile of each neighborhood archetype")
    fig.colorbar(image, ax=ax, label="Standard deviations from metro average")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "cluster_profiles_zscore.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    pca = PCA(n_components=2, random_state=SEED)
    scores = pca.fit_transform(z)
    fig, ax = plt.subplots(figsize=(8.5, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, 5))
    for cluster_id, color in zip(range(5), colors):
        mask = raw_cluster == cluster_id
        ax.scatter(scores[mask, 0], scores[mask, 1], s=24, alpha=0.65, color=color, label=ARCHETYPE_NAMES[cluster_id])
    ax.set(
        title="Neighborhood archetypes in two-dimensional PCA space",
        xlabel=f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)",
        ylabel=f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)",
    )
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "pca_clusters.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    ordered_names = list(ARCHETYPE_NAMES.values())
    box_data = [assignments.loc[assignments["Archetype"] == name, "Pct_AO0"] for name in ordered_names]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.boxplot(box_data, tick_labels=ordered_names, showfliers=False)
    ax.set(title="Zero-car household share differs across archetypes", ylabel="Share of households with no vehicle")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "zero_car_households_by_cluster.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    groups = [group["Pct_AO0"].to_numpy() for _, group in assignments.groupby("Cluster")]
    h_stat, p_value = kruskal(*groups)
    epsilon_squared = max(0.0, (h_stat - 5 + 1) / (len(assignments) - 5))
    seed_ari = stability.loc[stability["Check"] == "Random initialization",
                             "Adjusted_Rand_Index"]
    subsample_ari = stability.loc[stability["Check"] == "80% subsample",
                                  "Adjusted_Rand_Index"]
    hierarchy_ari = robustness.loc[
        robustness["Analysis"] == "Ward hierarchical clustering", "ARI_vs_base"
    ].iloc[0]

    summary = (
        "Neighborhood clustering validation summary\n"
        f"Rows: {len(assignments)}\n"
        "Features: D1B, D1C, D2A_EPHHM, D3B, D4A_Ranked, D5CRI\n"
        "Selected k: 5\n"
        f"Kruskal-Wallis H for zero-car share: {h_stat:.3f}\n"
        f"p-value: {p_value:.6g}\n"
        f"epsilon-squared effect size: {epsilon_squared:.3f}\n"
        f"Random-initialization ARI median: {seed_ari.median():.3f}\n"
        f"80% subsample ARI median: {subsample_ari.median():.3f}\n"
        f"80% subsample ARI 5th percentile: {subsample_ari.quantile(0.05):.3f}\n"
        f"Ward hierarchical ARI vs K-means: {hierarchy_ari:.3f}\n"
    )
    (OUTPUT_DIR / "analysis_summary.txt").write_text(summary, encoding="utf-8")
    print(profiles.to_string(index=False))
    print("\n" + summary)


if __name__ == "__main__":
    main()
