"""
验证LLM审查功能的正确性
使用 linux_kernel_cves_benchmark.json 中的CVE数据
对比 LLM分析+多模型审查 的结果与CVSS Ground Truth

使用方法:
  python scripts/validate_llm_review.py
  python scripts/validate_llm_review.py --limit 20
  python scripts/validate_llm_review.py --no-censorship  # 只测试单模型，跳过多模型审查
"""

import json
import os
import sys
import argparse
import time
from collections import defaultdict

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from server.service.LLM_layer import LLMAnalyzer
from server.service.LLM_censorship import LLMCensorship

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
BENCHMARK_PATH = os.path.join(DATA_DIR, "linux_kernel_cves_benchmark.json")
RESULTS_PATH = os.path.join(DATA_DIR, "validation_results.json")


def severity_to_score(severity: str) -> int:
    """严重等级 -> 数值分数，用于计算偏差"""
    mapping = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "None": 0}
    return mapping.get(severity, 0)


def validate(benchmark_path: str, limit: int = 0, no_censorship: bool = False):
    """运行验证"""

    if not os.path.exists(benchmark_path):
        print(f"基准数据集不存在: {benchmark_path}")
        print("请先运行: python scripts/extract_linux_kernel_cves.py")
        sys.exit(1)

    with open(benchmark_path, 'r', encoding='utf-8') as f:
        cves = json.load(f)

    # 只保留有CVSS评分和diff的
    cves = [c for c in cves if c.get("ground_truth_severity") and c.get("diff")]
    print(f"有效测试样本（有CVSS+diff）: {len(cves)}")

    if limit > 0:
        cves = cves[:limit]
        print(f"限制数量: {len(cves)}")

    # 初始化分析器
    print("\n初始化LLM分析器...")
    analyzer = LLMAnalyzer()
    censorship = None if no_censorship else LLMCensorship()

    if no_censorship:
        print("模式: 单模型分析（DeepSeek only）")
    else:
        available = list(censorship.clients.keys()) if censorship else []
        print(f"模式: 单模型分析 + 多模型审查 ({available})")

    # 逐条验证
    results = []
    for i, cve in enumerate(cves):
        cve_id = cve["cve_id"]
        commit_msg = cve.get("cmt_msg", cve.get("commit_message", ""))
        diff = cve.get("diff", "")
        ground_truth = cve["ground_truth_severity"]
        cvss_score = cve.get("cvss_score")

        print(f"\n[{i+1}/{len(cves)}] 分析 {cve_id} (Ground Truth: {ground_truth}, CVSS: {cvss_score})")

        try:
            # Step 1: 单模型分析
            analysis_result = analyzer.analyze_commit(commit_msg, diff)
            original_severity = analysis_result.get("severity", "None")
            is_security = analysis_result.get("is_security_related", False)

            print(f"  DeepSeek: severity={original_severity}, security_related={is_security}")

            # Step 2: 多模型审查
            final_severity = original_severity
            review_data = None

            if censorship and is_security:
                review_result = censorship.review_severity(
                    commit_message=commit_msg,
                    diff=diff,
                    original_analysis=analysis_result,
                    use_parallel=True
                )
                final_severity = review_result.final_severity
                review_data = censorship.to_dict(review_result)
                print(f"  审查结果: {original_severity} -> {final_severity} "
                      f"(加权分数: {review_result.weighted_score:.2f}, "
                      f"一致性: {review_result.consensus_rate:.2f})")

            # 计算偏差
            gt_score = severity_to_score(ground_truth)
            pred_score = severity_to_score(final_severity)
            deviation = pred_score - gt_score

            result = {
                "cve_id": cve_id,
                "cvss_score": cvss_score,
                "ground_truth_severity": ground_truth,
                "original_severity": original_severity,
                "final_severity": final_severity,
                "is_security_related": is_security,
                "deviation": deviation,
                "correct": final_severity == ground_truth,
                "adjacent": abs(deviation) <= 1,  # 相邻等级也算可接受
                "analysis_summary": analysis_result.get("summary", ""),
                "vulnerability_type": analysis_result.get("vulnerability_type"),
                "affected_subsystem": analysis_result.get("affected_subsystem"),
            }

            if review_data:
                result["consensus_rate"] = review_data.get("consensus_rate", 0)
                result["weighted_score"] = review_data.get("weighted_score", 0)
                result["voting_breakdown"] = review_data.get("voting_breakdown", {})
                result["severity_changed"] = original_severity != final_severity

            results.append(result)

            # 标记结果
            if result["correct"]:
                print(f"  ✓ 正确")
            elif result["adjacent"]:
                print(f"  ~ 相邻偏差 (偏差={deviation})")
            else:
                print(f"  ✗ 偏差较大 (偏差={deviation})")

        except Exception as e:
            print(f"  分析失败: {e}")
            results.append({
                "cve_id": cve_id,
                "error": str(e)
            })

    # 统计
    print("\n" + "=" * 60)
    print("验证结果统计")
    print("=" * 60)

    valid_results = [r for r in results if "error" not in r]
    error_count = len(results) - len(valid_results)

    total = len(valid_results)
    if total == 0:
        print("无有效结果")
        return

    exact_match = sum(1 for r in valid_results if r.get("correct"))
    adjacent_match = sum(1 for r in valid_results if r.get("adjacent"))
    avg_deviation = sum(abs(r.get("deviation", 0)) for r in valid_results) / total

    # 按等级统计
    by_gt = defaultdict(lambda: {"total": 0, "correct": 0, "predictions": []})
    for r in valid_results:
        gt = r.get("ground_truth_severity", "Unknown")
        by_gt[gt]["total"] += 1
        if r.get("correct"):
            by_gt[gt]["correct"] += 1
        by_gt[gt]["predictions"].append(r.get("final_severity", "None"))

    # 审查调整统计
    severity_changed = sum(1 for r in valid_results if r.get("severity_changed", False))
    changed_improved = sum(1 for r in valid_results
                          if r.get("severity_changed") and r.get("correct") or
                             (r.get("severity_changed") and r.get("adjacent") and not r.get("correct")))

    print(f"总样本数: {total} (失败: {error_count})")
    print(f"精确匹配率: {exact_match}/{total} ({exact_match/total*100:.1f}%)")
    print(f"相邻匹配率: {adjacent_match}/{total} ({adjacent_match/total*100:.1f}%)")
    print(f"平均偏差: {avg_deviation:.2f} 级")
    print(f"\n按Ground Truth等级:")
    for sev in ["Critical", "High", "Medium", "Low"]:
        if sev in by_gt:
            data = by_gt[sev]
            acc = data["correct"] / data["total"] * 100 if data["total"] > 0 else 0
            print(f"  {sev}: {data['correct']}/{data['total']} ({acc:.1f}%)")

    if not no_censorship:
        print(f"\n多模型审查统计:")
        print(f"  严重等级被调整: {severity_changed}/{total}")
        print(f"  调整后更准确: {changed_improved}/{severity_changed}" if severity_changed > 0 else "  无调整")

    # 混淆矩阵
    print(f"\n混淆矩阵 (行=Ground Truth, 列=预测):")
    severities = ["Critical", "High", "Medium", "Low", "None"]
    matrix = defaultdict(lambda: defaultdict(int))
    for r in valid_results:
        gt = r.get("ground_truth_severity", "Unknown")
        pred = r.get("final_severity", "None")
        matrix[gt][pred] += 1

    # 打印表头
    header = f"{'GT\\Pred':<12}"
    for s in severities:
        header += f"{s:<12}"
    print(header)
    for gt_sev in severities:
        row = f"{gt_sev:<12}"
        for pred_sev in severities:
            row += f"{matrix[gt_sev].get(pred_sev, 0):<12}"
        print(row)

    # 保存详细结果
    output = {
        "summary": {
            "total": total,
            "errors": error_count,
            "exact_match": exact_match,
            "exact_match_rate": exact_match / total if total > 0 else 0,
            "adjacent_match": adjacent_match,
            "adjacent_match_rate": adjacent_match / total if total > 0 else 0,
            "avg_deviation": avg_deviation,
            "by_ground_truth": {k: {"total": v["total"], "correct": v["correct"]}
                               for k, v in by_gt.items()},
            "confusion_matrix": {k: dict(v) for k, v in matrix.items()}
        },
        "results": results
    }

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n详细结果已保存到: {RESULTS_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="验证LLM审查功能正确性")
    parser.add_argument("--limit", type=int, default=0, help="限制测试数量")
    parser.add_argument("--no-censorship", action="store_true", help="跳过多模型审查")
    args = parser.parse_args()

    validate(BENCHMARK_PATH, limit=args.limit, no_censorship=args.no_censorship)
