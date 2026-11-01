from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parent
path = base / "results" / "ablation" / "pfiv_ablation_results.csv"
out = base / "results" / "ablation" / "pfiv_score_without_vs_with_pfiv.png"

df = pd.read_csv(path)
plot = df[["Test Case", "Baseline Without PFIV Score", "Full System With PFIV Score"]].copy()
plot = plot.set_index("Test Case")
plot.plot(kind="bar", figsize=(11,6))
plt.ylabel("Risk Score")
plt.xlabel("Controlled Test Case")
plt.title("PFIV Ablation: Risk Score Without vs With PFIV")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig(out, dpi=300, bbox_inches="tight")
plt.close()
print(out)
