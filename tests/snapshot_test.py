"""
Snapshot Testing for Dashboard Diffusion System
Validates that reasoning runs produce expected panel configurations
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import hashlib

sys.path.append('/home/tjm/code/demo')

from tests.golden_outputs import (
    get_all_scenarios,
    get_scenario,
    validate_output_against_golden,
)


class SnapshotTester:
    """Test runner for golden output validation"""
    
    def __init__(self, kernel_base_url: str = "http://127.0.0.1:8081"):
        self.kernel_url = kernel_base_url
        self.results: List[Dict[str, Any]] = []
    
    async def run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single test scenario
        
        Returns test result with panels and validation
        """
        import aiohttp
        
        request = {
            "module": scenario["module"],
            "prompt": scenario["prompt"],
            "run_mode": "stable",
            "allow_web_fetch": False,
        }
        
        panels: List[Dict[str, Any]] = []
        reasoning_text = ""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.kernel_url}/reason",
                    json=request,
                    headers={"Accept": "text/event-stream"}
                ) as response:
                    if response.status != 200:
                        return {
                            "scenario": scenario["name"],
                            "success": False,
                            "error": f"HTTP {response.status}",
                        }
                    
                    # Parse SSE stream
                    last_event_type = None
                    buffer = ""
                    
                    async for chunk in response.content.iter_chunked(1024):
                        buffer += chunk.decode('utf-8')
                        lines = buffer.split('\n')
                        buffer = lines.pop() if lines else ""
                        
                        for line in lines:
                            line = line.strip()
                            if not line or line.startswith(':'):
                                continue
                            
                            if line.startswith('event:'):
                                last_event_type = line[6:].strip()
                                continue
                            
                            if line.startswith('data:'):
                                data_str = line[5:].strip()
                                try:
                                    data = json.loads(data_str)
                                    
                                    if last_event_type == 'intent':
                                        # Extract panel from intent
                                        if data.get('action') == 'show_panel':
                                            panels.append({
                                                "type": data.get("panel"),
                                                "data": data.get("data", {}),
                                                "id": data.get("id"),
                                            })
                                    
                                    elif last_event_type == 'token':
                                        reasoning_text += data.get("token", "")
                                    
                                    elif last_event_type == 'final':
                                        break
                                
                                except json.JSONDecodeError:
                                    pass
        
        except Exception as e:
            return {
                "scenario": scenario["name"],
                "success": False,
                "error": str(e),
            }
        
        # Validate output against golden
        validation = validate_output_against_golden(panels, scenario)
        
        # Check reasoning content
        reasoning_keywords = scenario.get("reasoning_must_contain", [])
        missing_keywords = [
            kw for kw in reasoning_keywords
            if kw.lower() not in reasoning_text.lower()
        ]
        
        if missing_keywords:
            validation["warnings"].append(
                f"Reasoning missing keywords: {', '.join(missing_keywords)}"
            )
        
        # Compute hash of panel structure for regression detection
        panel_structure = [
            {"type": p["type"], "fields": sorted(p.get("data", {}).keys())}
            for p in panels
        ]
        structure_hash = hashlib.md5(
            json.dumps(panel_structure, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        return {
            "scenario": scenario["name"],
            "success": validation["valid"],
            "panels": panels,
            "panel_count": len(panels),
            "validation": validation,
            "structure_hash": structure_hash,
            "reasoning_length": len(reasoning_text),
            "reasoning_sample": reasoning_text[:200] if reasoning_text else "",
        }
    
    async def run_all_scenarios(self) -> Dict[str, Any]:
        """Run all golden output scenarios"""
        scenarios = get_all_scenarios()
        
        print(f"Running {len(scenarios)} test scenarios...")
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n[{i}/{len(scenarios)}] Testing: {scenario['name']}")
            print(f"  Module: {scenario['module']}")
            print(f"  Prompt: {scenario['prompt'][:60]}...")
            
            result = await self.run_scenario(scenario)
            self.results.append(result)
            
            if result["success"]:
                print(f"  ✓ PASS - {result['panel_count']} panels, hash: {result['structure_hash']}")
            else:
                print(f"  ✗ FAIL")
                if "error" in result:
                    print(f"    Error: {result['error']}")
                if "validation" in result:
                    for error in result["validation"].get("errors", []):
                        print(f"    - {error}")
        
        # Summary
        passed = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - passed
        
        summary = {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(self.results) if self.results else 0,
            "results": self.results,
        }
        
        return summary
    
    def save_results(self, output_path: Path):
        """Save test results to JSON file"""
        summary = {
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r["success"]),
            "failed": sum(1 for r in self.results if not r["success"]),
            "results": self.results,
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nResults saved to: {output_path}")


async def main():
    """Main test runner"""
    tester = SnapshotTester()
    
    summary = await tester.run_all_scenarios()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total scenarios: {summary['total']}")
    print(f"Passed: {summary['passed']} ✓")
    print(f"Failed: {summary['failed']} ✗")
    print(f"Pass rate: {summary['pass_rate']*100:.1f}%")
    print("="*60)
    
    # Save results
    output_path = Path("/home/tjm/code/demo/tests/snapshot_results.json")
    tester.save_results(output_path)
    
    # Exit with error code if any tests failed
    if summary['failed'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
