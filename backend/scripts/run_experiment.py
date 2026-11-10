import argparse
import sys
import httpx
import time

def run_experiment(base_url, v1, v2):
    print(f"Starting A/B Red Team Experiment: {v1} vs {v2}")
    
    try:
        response = httpx.post(
            f"{base_url}/api/experiments/compare",
            json={"version_a": v1, "version_b": v2},
            timeout=120.0
        )
        response.raise_for_status()
        result = response.json()
        
        print("\n--- EXPERIMENT RESULTS ---")
        print(f"Winner: {result['winner']}")
        print(f"Reason: {result['reason']}")
        
        print("\nBreakdown:")
        print(f"[{v1}] Risk Score: {result['version_a_score']:.2f}")
        print(f"[{v2}] Risk Score: {result['version_b_score']:.2f}")
        
    except Exception as e:
        print(f"Error running experiment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an A/B red team experiment")
    parser.add_argument("--v1", type=str, required=True, help="Agent Version A")
    parser.add_argument("--v2", type=str, required=True, help="Agent Version B")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:8000", help="API Base URL")
    
    args = parser.parse_args()
    run_experiment(args.url, args.v1, args.v2)
