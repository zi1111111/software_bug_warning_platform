"""
从 linux_kernel_cves 数据集提取Linux内核CVE，并从NVD API补充CVSS评分
用于验证LLM审查功能的正确性

使用方法：
1. 克隆数据集:
   git clone https://github.com/nluedtke/linux_kernel_cves.git data/linux_kernel_cves
   (如果网络不好可以用镜像或手动下载zip)

2. 安装依赖:
   pip install nvdlib

3. 运行:
   python scripts/extract_linux_kernel_cves.py
   python scripts/extract_linux_kernel_cves.py --limit 50   # 只取50条
   python scripts/extract_linux_kernel_cves.py --skip-nvd    # 跳过NVD查询（无CVSS）

输出: data/linux_kernel_cves_benchmark.json
"""

import json
import os
import sys
import glob
import time
import argparse

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
REPO_DIR = os.path.join(DATA_DIR, "linux_kernel_cves")
OUTPUT_PATH = os.path.join(DATA_DIR, "linux_kernel_cves_benchmark.json")

# NVD API有速率限制：每30秒5次请求（无API key），每30秒50次（有API key）
NVD_REQUEST_INTERVAL = 6  # 秒，无API key时每次请求间隔


def cvss_to_severity(score):
    """CVSS评分 -> 严重等级映射"""
    if score is None:
        return None
    score = float(score)
    if score >= 9.0:
        return "Critical"
    elif score >= 7.0:
        return "High"
    elif score >= 4.0:
        return "Medium"
    else:
        return "Low"


def load_cves_from_repo(repo_dir: str) -> list:
    """从linux_kernel_cves仓库的JSON文件中加载所有CVE"""
    cves_dir = os.path.join(repo_dir, "CVEs")
    if not os.path.exists(cves_dir):
        print(f"错误: 找不到CVEs目录: {cves_dir}")
        print("请先克隆数据集:")
        print(f"  git clone https://github.com/nluedtke/linux_kernel_cves.git {repo_dir}")
        sys.exit(1)

    all_cves = []
    json_files = glob.glob(os.path.join(cves_dir, "**", "*.json"), recursive=True)
    print(f"找到 {len(json_files)} 个CVE JSON文件")

    for fpath in json_files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # linux_kernel_cves的JSON格式: 顶层key就是CVE ID
            # 每个文件可能包含一个或多个CVE
            for cve_id, cve_data in data.items():
                if not cve_id.startswith("CVE-"):
                    continue

                fixes = cve_data.get("fixes", "")
                cmt_msg = cve_data.get("cmt_msg", "")
                breaks = cve_data.get("breaks", "")

                # 只保留有fixing commit的CVE（才能获取diff）
                if not fixes:
                    continue

                all_cves.append({
                    "cve_id": cve_id,
                    "fixes": fixes,
                    "breaks": breaks,
                    "cmt_msg": cmt_msg,
                    "affected_versions": cve_data.get("affected_versions", ""),
                })
        except Exception as e:
            continue

    print(f"有效CVE（有fixing commit）: {len(all_cves)}")
    return all_cves


def fetch_cvss_from_nvd(cve_id: str) -> dict:
    """从NVD API查询CVSS评分"""
    try:
        import nvdlib
        results = nvdlib.searchCVE(cveId=cve_id)
        if results:
            cve = results[0]
            # 优先CVSS v3.1，其次v3，最后v2
            score = None
            severity = None
            if hasattr(cve, 'v31score') and cve.v31score:
                score = cve.v31score
                severity = cve.v31severity
            elif hasattr(cve, 'v30score') and cve.v30score:
                score = cve.v30score
                severity = cve.v30severity
            elif hasattr(cve, 'v2score') and cve.v2score:
                score = cve.v2score
                severity = cve.v2severity

            description = ""
            if hasattr(cve, 'descriptions') and cve.descriptions:
                for desc in cve.descriptions:
                    if desc.lang == 'en':
                        description = desc.value
                        break

            return {
                "cvss_score": score,
                "cvss_severity": severity,
                "nvd_description": description
            }
    except ImportError:
        print("nvdlib未安装，请运行: pip install nvdlib")
        return {}
    except Exception as e:
        print(f"  NVD查询失败 {cve_id}: {e}")
        return {}


def fetch_cvss_from_nvd_api(cve_id: str) -> dict:
    """从NVD REST API直接查询CVSS评分（无需nvdlib依赖）"""
    import urllib.request
    import urllib.error

    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
    headers = {"Accept": "application/json"}

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        vulnerabilities = data.get("vulnerabilities", [])
        if not vulnerabilities:
            return {}

        cve_data = vulnerabilities[0].get("cve", {})
        metrics = cve_data.get("metrics", {})

        # 优先CVSS v3.1
        score = None
        severity = None
        cvss_v31 = metrics.get("cvssMetricV31", [])
        cvss_v30 = metrics.get("cvssMetricV30", [])
        cvss_v2 = metrics.get("cvssMetricV2", [])

        if cvss_v31:
            cvss_data = cvss_v31[0].get("cvssData", {})
            score = cvss_data.get("baseScore")
            severity = cvss_data.get("baseSeverity")
        elif cvss_v30:
            cvss_data = cvss_v30[0].get("cvssData", {})
            score = cvss_data.get("baseScore")
            severity = cvss_data.get("baseSeverity")
        elif cvss_v2:
            cvss_data = cvss_v2[0].get("cvssData", {})
            score = cvss_data.get("baseScore")
            severity = cvss_data.get("baseSeverity")

        # 获取英文描述
        description = ""
        descriptions = cve_data.get("descriptions", [])
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break

        return {
            "cvss_score": score,
            "cvss_severity": severity,
            "nvd_description": description
        }

    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"  NVD速率限制 {cve_id}，等待更长时间...")
        return {}
    except Exception as e:
        print(f"  NVD查询失败 {cve_id}: {e}")
        return {}


def get_commit_diff_from_github(commit_hash: str) -> str:
    """从GitHub API获取commit diff"""
    import urllib.request
    import urllib.error

    url = f"https://api.github.com/repos/torvalds/linux/commits/{commit_hash}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "CVE-Benchmark-Tool"
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            diff = resp.read().decode('utf-8')
            # 截断过长的diff
            if len(diff) > 8000:
                diff = diff[:8000] + "\n... (truncated)"
            return diff
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return ""  # commit不在mainline
        return ""
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser(description="提取Linux内核CVE基准数据集")
    parser.add_argument("--limit", type=int, default=0, help="限制提取数量（0=全部）")
    parser.add_argument("--skip-nvd", action="store_true", help="跳过NVD CVSS查询")
    parser.add_argument("--skip-diff", action="store_true", help="跳过GitHub diff获取")
    parser.add_argument("--year", type=str, default=None, help="只提取指定年份的CVE（如2024）")
    parser.add_argument("--min-year", type=int, default=2020, help="最早年份（默认2020）")
    args = parser.parse_args()

    # 1. 加载CVE数据
    cves = load_cves_from_repo(REPO_DIR)

    # 2. 按年份筛选
    if args.year:
        cves = [c for c in cves if args.year in c['cve_id']]
        print(f"筛选年份 {args.year}: {len(cves)} 条")

    if args.min_year:
        cves = [c for c in cves if int(c['cve_id'].split('-')[1]) >= args.min_year]
        print(f"筛选 >= {args.min_year}: {len(cves)} 条")

    # 3. 限制数量
    if args.limit > 0:
        cves = cves[:args.limit]
        print(f"限制数量: {len(cves)} 条")

    # 4. 补充NVD CVSS评分
    if not args.skip_nvd:
        print(f"\n开始从NVD获取CVSS评分（每请求间隔{NVD_REQUEST_INTERVAL}秒）...")
        success_count = 0
        for i, cve in enumerate(cves):
            print(f"  [{i+1}/{len(cves)}] 查询 {cve['cve_id']}...")
            nvd_info = fetch_cvss_from_nvd_api(cve['cve_id'])
            if nvd_info:
                cve.update(nvd_info)
                success_count += 1
            # NVD速率限制
            if i < len(cves) - 1:
                time.sleep(NVD_REQUEST_INTERVAL)

        print(f"NVD查询完成: 成功{success_count}/{len(cves)}")
    else:
        print("跳过NVD查询")

    # 5. 获取commit diff
    if not args.skip_diff:
        print(f"\n开始从GitHub获取commit diff...")
        diff_count = 0
        for i, cve in enumerate(cves):
            commit_hash = cve.get("fixes", "")
            if commit_hash and len(commit_hash) >= 7:
                print(f"  [{i+1}/{len(cves)}] 获取diff {commit_hash[:12]}...")
                diff = get_commit_diff_from_github(commit_hash)
                cve["diff"] = diff
                if diff:
                    diff_count += 1
                # GitHub API限制：每分钟60次（无token）
                time.sleep(1)
            else:
                cve["diff"] = ""

        print(f"Diff获取完成: 成功{diff_count}/{len(cves)}")
    else:
        print("跳过diff获取")

    # 6. 计算Ground Truth
    for cve in cves:
        cvss_score = cve.get("cvss_score")
        cve["ground_truth_severity"] = cvss_to_severity(cvss_score)

    # 7. 统计
    severity_dist = {}
    has_cvss = 0
    has_diff = 0
    for cve in cves:
        sev = cve.get("ground_truth_severity") or "Unknown"
        severity_dist[sev] = severity_dist.get(sev, 0) + 1
        if cve.get("cvss_score") is not None:
            has_cvss += 1
        if cve.get("diff"):
            has_diff += 1

    print(f"\n===== 数据集统计 =====")
    print(f"总数: {len(cves)}")
    print(f"有CVSS评分: {has_cvss}")
    print(f"有Diff: {has_diff}")
    print(f"严重等级分布: {json.dumps(severity_dist, ensure_ascii=False)}")

    # 8. 保存
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(cves, f, ensure_ascii=False, indent=2)

    print(f"\n已保存到: {OUTPUT_PATH}")
    print(f"\n下一步: 使用此数据集验证LLM审查功能")
    print(f"  python scripts/validate_llm_review.py")


if __name__ == "__main__":
    main()
