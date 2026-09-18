"""
Script: scripts/package_release.py
Phase 16: CLI executable to package, hash, and verify production release bundle.
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.packaging.bundle import package_release_bundle, load_release_bundle


def main():
    parser = argparse.ArgumentParser(description="Package Comorbidity Prediction Release Bundle")
    parser.add_argument("--output_dir", type=str, default="models/release_v1", help="Output directory for bundle")
    parser.add_argument("--version", type=str, default="1.0.0", help="Release version string")
    parser.add_argument("--description", type=str, default="Production Comorbidity Ensemble & Calibration Release v1.0.0", help="Release description")
    parser.add_argument("--verify", action="store_true", default=True, help="Verify integrity after packaging")
    
    args = parser.parse_args()
    
    # 1. Package
    manifest = package_release_bundle(
        output_dir=args.output_dir,
        version=args.version,
        description=args.description
    )
    
    # 2. Verify
    if args.verify:
        print("\nLoading and verifying packaged release bundle in fresh instance...")
        bundle = load_release_bundle(args.output_dir)
        integrity = bundle.verify_integrity()
        n_passed = sum(1 for v in integrity.values() if v)
        n_total = len(integrity)
        print(f"Bundle Integrity: {n_passed}/{n_total} artifacts verified successfully.")
        assert n_passed == n_total, "Integrity verification failure!"
        print("Release Bundle is READY for deployment.")


if __name__ == "__main__":
    main()

