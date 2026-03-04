import json, sys, os
from datetime import datetime

out_dir = sys.argv[1]
digest_path = os.path.join(out_dir, "digest_latest.json")
gh_path = os.path.join(out_dir, "github_trending.json")

digest = {}
gh = []
try:
    with open(digest_path) as f: digest = json.load(f)
except: pass
try:
    with open(gh_path) as f: gh = json.load(f)
except: pass

summary = {
    "fetchedAt": datetime.now().isoformat(),
    "candidateCount": len(digest.get("candidates", [])),
    "githubCount": len(gh),
    "categories": digest.get("stats", {}).get("byCategoryCandidates", {}),
    "ready": True
}
with open(os.path.join(out_dir, "status.json"), "w") as f:
    json.dump(summary, f, ensure_ascii=False)
print(json.dumps(summary, ensure_ascii=False))
