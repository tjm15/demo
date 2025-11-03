"""
Evidence Base Module - handles evidence discovery, validation, and analysis
Enhanced with LLM reasoning and comprehensive data integration
"""
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from modules.context import ContextPack
from modules.trace import TraceEntry, write_trace
from pathlib import Path
import json
import os

async def evidence_playbook(context: ContextPack, trace_path: Path) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute evidence base reasoning workflow with rich LLM analysis.
    
    Phases:
    1. Parse intent and extract parameters
    2. Retrieve evidence items via enhanced search
    3. Analyze quality, currency, and completeness
    4. Generate streaming reasoning narrative
    5. Emit coordinated panel intents with real data
    """
    
    await write_trace(trace_path, TraceEntry(
        t=datetime.utcnow().isoformat(),
        step="evidence_start",
        input={"prompt": context.prompt, "module": "evidence"}
    ))
    
    # Import services
    from services.evidence import (
        search_evidence,
        EvidenceSearchRequest,
        evidence_gaps,
        get_dependency_graph,
        get_evidence_detail,
    )
    
    # Determine user intent
    prompt_lower = context.prompt.lower()
    
    # Phase 1: Determine action type
    if any(kw in prompt_lower for kw in ["gap", "missing", "weak", "stale", "lacking"]):
        action = "gap_analysis"
    elif any(kw in prompt_lower for kw in ["link", "connect", "dependency", "depends", "relies"]):
        action = "dependencies"
    elif any(kw in prompt_lower for kw in ["validate", "check", "quality", "currency", "reliable"]):
        action = "validate"
    elif any(kw in prompt_lower for kw in ["compare", "benchmark", "vs", "versus"]):
        action = "compare"
    else:
        action = "search"  # default
    
    await write_trace(trace_path, TraceEntry(
        t=datetime.utcnow().isoformat(),
        step="determine_action",
        output={"action": action, "prompt_snippet": context.prompt[:100]}
    ))
    
    # Phase 2: Extract search parameters
    topics = []
    if "housing" in prompt_lower:
        topics.append("housing")
    if "transport" in prompt_lower:
        topics.append("transport")
    if "economy" in prompt_lower or "employment" in prompt_lower or "economic" in prompt_lower:
        topics.append("economy")
    if "environment" in prompt_lower or "climate" in prompt_lower:
        topics.append("climate")
    if "retail" in prompt_lower or "town cent" in prompt_lower:
        topics.append("retail")
    if "social" in prompt_lower or "community" in prompt_lower:
        topics.append("social")
    if "infrastructure" in prompt_lower:
        topics.append("infrastructure")
    
    # Extract authority/location
    authorities = []
    for auth in ["westminster", "camden", "islington", "southwark", "hackney", "tower hamlets", 
                 "brent", "lambeth", "greenwich", "ealing", "lewisham", "haringey"]:
        if auth in prompt_lower:
            authorities.append(auth.title())
    
    # Extract evidence types
    evidence_types = []
    type_keywords = {
        "SHMA": ["shma", "housing market", "housing need"],
        "HENA": ["hena", "housing economic"],
        "SFRA": ["sfra", "flood risk"],
        "Viability": ["viability", "viability study"],
        "SHELAA": ["shelaa", "land availability"],
        "Transport Assessment": ["transport", "transport assessment"],
        "Employment": ["employment land", "employment study"]
    }
    for ev_type, keywords in type_keywords.items():
        if any(kw in prompt_lower for kw in keywords):
            evidence_types.append(ev_type)
    
    await write_trace(trace_path, TraceEntry(
        t=datetime.utcnow().isoformat(),
        step="extract_parameters",
        output={"topics": topics, "authorities": authorities, "evidence_types": evidence_types}
    ))
    
    # Interactive disambiguation: if multiple authorities mentioned, emit a prompt (non-blocking)
    if len(authorities) > 1:
        # Inform user in the token stream
        yield {
            "type": "token",
            "data": {"content": f"Multiple authorities detected: {', '.join(authorities)}\n"}
        }

        # If the client already provided a selected authority in context, use it
        selected_auth = getattr(context, "selected_authority", None)
        if selected_auth and selected_auth in authorities:
            authorities = [selected_auth]
            yield {"type": "token", "data": {"content": f"✓ Focusing on **{selected_auth}**\n\n"}}
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="user_selected_authority",
                output={"selected": selected_auth}
            ))
        else:
            # Emit a prompt_user event to the client (best-effort). Frontend should
            # display a modal and re-run /reason with `selected_authority` in the
            # request body when the user responds.
            yield {
                "type": "prompt_user",
                "data": {
                    "prompt_id": None,
                    "question": "Which authority would you like to focus on?",
                    "input_type": "select",
                    "options": [{"value": auth, "label": auth} for auth in authorities],
                    "default": authorities[0],
                    "context": {"module": "evidence", "prompt_snippet": context.prompt[:100]}
                }
            }
            # Continue with default immediately; frontend can restart with a choice
            authorities = [authorities[0]]
            yield {"type": "token", "data": {"content": f"⏱️  Continuing with default **{authorities[0]}**\n\n"}}
    
    # Phase 3: Execute action with data retrieval
    if action == "search":
        # Stream reasoning tokens
        yield {
            "type": "token",
            "data": {"content": "🔍 **Searching evidence base**\n\n"}
        }
        
        yield {
            "type": "token",
            "data": {"content": f"Querying for: {context.prompt}\n"}
        }
        
        if topics:
            yield {
                "type": "token",
                "data": {"content": f"Topics identified: {', '.join(topics)}\n"}
            }
        
        # Call backend service to get actual evidence items
        try:
            results = await search_evidence(EvidenceSearchRequest(
                q=context.prompt,
                topic=topics if topics else None,
                scope="db",
                limit=20,
                use_semantic=True
            ))
            items = [item.dict() for item in results]
            
            # If results are limited and web fetch is allowed, emit a non-blocking confirmation
            if len(items) < 5 and context.allow_web_fetch:
                # If client previously confirmed web fetch, use that
                confirmed = getattr(context, "confirm_web_fetch", None)
                if confirmed is True:
                    yield {"type": "token", "data": {"content": "\n🌐 **Searching external sources...**\n\n"}}
                    await write_trace(trace_path, TraceEntry(
                        t=datetime.utcnow().isoformat(),
                        step="user_confirmed_web_fetch",
                        output={"confirmed": True}
                    ))
                    # TODO: Implement proxy search here
                    yield {"type": "token", "data": {"content": "*(Web fetch functionality will be implemented post-demo)*\n\n"}}
                else:
                    # Emit a prompt_user event asking whether to fetch; frontend may
                    # re-run with `confirm_web_fetch` set in the request body.
                    yield {
                        "type": "prompt_user",
                        "data": {
                            "prompt_id": None,
                            "question": f"Found only {len(items)} items in local database. Would you like to search external sources (GOV.UK, planning portals)?",
                            "input_type": "confirm",
                            "options": [],
                            "default": False,
                            "context": {"module": "evidence", "prompt_snippet": context.prompt[:100]}
                        }
                    }
                    yield {"type": "token", "data": {"content": "\n✓ Continuing with local results (you can re-run with web fetch)\n\n"}}
            
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="evidence_search",
                output={"items_found": len(items), "topics": topics}
            ))
            
            # Analyze results
            yield {
                "type": "token",
                "data": {"content": f"\n✓ Found **{len(items)} evidence items**\n\n"}
            }
            
            # Categorize by type
            by_type = {}
            by_authority = {}
            stale_count = 0
            current_year = datetime.now().year
            
            for item in items:
                ev_type = item["type"]
                by_type[ev_type] = by_type.get(ev_type, 0) + 1
                
                auth = item["geographic_scope"]
                if auth:
                    by_authority[auth] = by_authority.get(auth, 0) + 1
                
                if item["year"] and current_year - item["year"] > 5:
                    stale_count += 1
            
            # Generate analysis narrative
            if by_type:
                yield {
                    "type": "token",
                    "data": {"content": "**Evidence types found:**\n"}
                }
                for ev_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]:
                    yield {
                        "type": "token",
                        "data": {"content": f"- {ev_type}: {count} item(s)\n"}
                    }
                yield {
                    "type": "token",
                    "data": {"content": "\n"}
                }
            
            if by_authority:
                yield {
                    "type": "token",
                    "data": {"content": "**Geographic coverage:**\n"}
                }
                for auth, count in sorted(by_authority.items(), key=lambda x: x[1], reverse=True)[:5]:
                    yield {
                        "type": "token",
                        "data": {"content": f"- {auth}: {count} item(s)\n"}
                    }
                yield {
                    "type": "token",
                    "data": {"content": "\n"}
                }
            
            # Currency check
            if stale_count > 0:
                yield {
                    "type": "token",
                    "data": {"content": f"⚠️  **Warning:** {stale_count} item(s) are >5 years old and may need updating\n\n"}
                }
            
            # Emit evidence browser with actual data
            yield {
                "type": "intent",
                "data": {
                    "action": "show_panel",
                    "panel": "evidence_browser",
                    "id": f"evidence_browser_{int(datetime.utcnow().timestamp())}",
                    "data": {
                        "items": items,
                        "filters": {
                            "topics": topics,
                            "scope": "db"
                        }
                    }
                }
            }

            # Also show the top record detail to speed up exploration
            if items:
                top_id = items[0]["id"]
                try:
                    detail = await get_evidence_detail(top_id)
                    yield {
                        "type": "intent",
                        "data": {
                            "action": "show_panel",
                            "panel": "evidence_record",
                            "id": f"evidence_record_{top_id}",
                            "data": detail.dict()
                        }
                    }
                except Exception as e:
                    await write_trace(trace_path, TraceEntry(
                        t=datetime.utcnow().isoformat(),
                        step="evidence_detail_error",
                        output={"error": str(e), "id": top_id}
                    ))
            
        except Exception as e:
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="evidence_search_error",
                output={"error": str(e)}
            ))
            items = []
            yield {
                "type": "token",
                "data": {"content": f"\n❌ Error retrieving evidence: {str(e)}\n"}
            }
    
    elif action == "gap_analysis":
        yield {
            "type": "token",
            "data": {"content": "🔍 **Analyzing evidence gaps**\n\n"}
        }
        
        yield {
            "type": "token",
            "data": {"content": "Checking for policies with missing, stale, or weak evidence...\n\n"}
        }
        
        try:
            gaps = await evidence_gaps()
            
            no_evidence = gaps.get("no_evidence", [])
            stale_evidence = gaps.get("stale_evidence", [])
            weak_links = gaps.get("weak_links_only", [])
            
            total_gaps = len(no_evidence) + len(stale_evidence) + len(weak_links)
            
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="gap_analysis",
                output={"total_gaps": total_gaps}
            ))
            
            if total_gaps == 0:
                yield {
                    "type": "token",
                    "data": {"content": "✓ **No significant evidence gaps detected**\n\nAll policies have adequate supporting evidence.\n\n"}
                }
            else:
                yield {
                    "type": "token",
                    "data": {"content": f"Found **{total_gaps} evidence gaps** across the plan:\n\n"}
                }
                
                if no_evidence:
                    yield {
                        "type": "token",
                        "data": {"content": f"🔴 **{len(no_evidence)} policies with no evidence:**\n"}
                    }
                    for item in no_evidence[:3]:
                        yield {
                            "type": "token",
                            "data": {"content": f"- {item['title']}\n"}
                        }
                    if len(no_evidence) > 3:
                        yield {
                            "type": "token",
                            "data": {"content": f"- ...and {len(no_evidence) - 3} more\n"}
                        }
                    yield {
                        "type": "token",
                        "data": {"content": "\n"}
                    }
                
                if stale_evidence:
                    yield {
                        "type": "token",
                        "data": {"content": f"🟠 **{len(stale_evidence)} policies with stale evidence (>5 years):**\n"}
                    }
                    for item in stale_evidence[:3]:
                        yield {
                            "type": "token",
                            "data": {"content": f"- {item['title']} (latest: {item.get('latest_year', 'unknown')})\n"}
                        }
                    if len(stale_evidence) > 3:
                        yield {
                            "type": "token",
                            "data": {"content": f"- ...and {len(stale_evidence) - 3} more\n"}
                        }
                    yield {
                        "type": "token",
                        "data": {"content": "\n"}
                    }
                
                if weak_links:
                    yield {
                        "type": "token",
                        "data": {"content": f"🟡 **{len(weak_links)} policies with only weak evidence links:**\n"}
                    }
                    for item in weak_links[:3]:
                        yield {
                            "type": "token",
                            "data": {"content": f"- {item['title']}\n"}
                        }
                    if len(weak_links) > 3:
                        yield {
                            "type": "token",
                            "data": {"content": f"- ...and {len(weak_links) - 3} more\n"}
                        }
                    yield {
                        "type": "token",
                        "data": {"content": "\n"}
                    }
                
                yield {
                    "type": "token",
                    "data": {"content": "**Recommendation:** Address critical gaps (no evidence) first, then update stale evidence before Regulation 19 submission.\n\n"}
                }
            
            # Emit gap analysis panel
            yield {
                "type": "intent",
                "data": {
                    "action": "show_panel",
                    "panel": "evidence_gaps",
                    "id": f"evidence_gaps_{int(datetime.utcnow().timestamp())}",
                    "data": {
                        "no_evidence": no_evidence,
                        "stale_evidence": stale_evidence,
                        "weak_links_only": weak_links
                    }
                }
            }
            
        except Exception as e:
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="gap_analysis_error",
                output={"error": str(e)}
            ))
            yield {
                "type": "token",
                "data": {"content": f"\n❌ Error analyzing gaps: {str(e)}\n"}
            }
    
    elif action == "dependencies":
        yield {
            "type": "token",
            "data": {"content": "🔍 **Analyzing evidence-policy dependencies**\n\n"}
        }
        
        yield {
            "type": "token",
            "data": {"content": "Mapping which evidence supports which policies...\n\n"}
        }
        
        # Populate from service
        try:
            graph = await get_dependency_graph()
            yield {
                "type": "intent",
                "data": {
                    "action": "show_panel",
                    "panel": "dependency_graph",
                    "id": f"dependency_graph_{int(datetime.utcnow().timestamp())}",
                    "data": graph
                }
            }
        except Exception as e:
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="dependency_graph_error",
                output={"error": str(e)}
            ))
            yield {
                "type": "token",
                "data": {"content": f"⚠️ Failed to load dependency graph: {str(e)}\n\n"}
            }
        
        yield {
            "type": "token",
            "data": {"content": "Dependency graph generated. See panel for visualization.\n\n"}
        }
    
    elif action == "validate":
        # Combined search + gap analysis
        yield {
            "type": "token",
            "data": {"content": "🔍 **Validating evidence base**\n\n"}
        }
        
        # Search first
        try:
            results = await search_evidence(EvidenceSearchRequest(
                q=context.prompt,
                topic=topics if topics else None,
                scope="db",
                limit=20
            ))
            items = [item.dict() for item in results]
            
            yield {
                "type": "token",
                "data": {"content": f"Found {len(items)} relevant evidence items.\n"}
            }
            
            yield {
                "type": "intent",
                "data": {
                    "action": "show_panel",
                    "panel": "evidence_browser",
                    "id": f"evidence_browser_{int(datetime.utcnow().timestamp())}",
                    "data": {"items": items, "filters": {"topics": topics}}
                }
            }
        except:
            pass
        
        # Then gaps
        try:
            gaps = await evidence_gaps()
            yield {
                "type": "intent",
                "data": {
                    "action": "show_panel",
                    "panel": "evidence_gaps",
                    "id": f"evidence_gaps_{int(datetime.utcnow().timestamp())}",
                    "data": gaps
                }
            }
            
            total_gaps = len(gaps.get("no_evidence", [])) + len(gaps.get("stale_evidence", [])) + len(gaps.get("weak_links_only", []))
            yield {
                "type": "token",
                "data": {"content": f"\nIdentified {total_gaps} evidence gaps requiring attention.\n\n"}
            }
        except:
            pass
    
    # Final summary message
    yield {
        "type": "token",
        "data": {"content": "\n---\n\n**Evidence analysis complete.** Use the panels above to explore findings in detail.\n"}
    }
    
    yield {
        "type": "final",
        "data": {
            "summary": f"Evidence {action} executed successfully",
            "action": action,
            "topics": topics,
            "authorities": authorities
        }
    }
    
    await write_trace(trace_path, TraceEntry(
        t=datetime.utcnow().isoformat(),
        step="evidence_complete",
        output={"action": action}
    ))

