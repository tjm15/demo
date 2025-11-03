"""
Seed comprehensive evidence data for demonstration
Covers all evidence types with versions and policy links
Can be run via docker exec or directly if psycopg is installed
"""
import sys
import json
from datetime import datetime

# Comprehensive evidence dataset covering all required types
SAMPLE_EVIDENCE = [
    # ========== HOUSING EVIDENCE (10 items) ==========
    {
        "title": "Westminster Strategic Housing Market Assessment 2024",
        "type": "SHMA",
        "topic_tags": ["housing", "economy"],
        "geographic_scope": "Westminster City Council",
        "author": "GL Hearn",
        "publisher": "Westminster City Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Identified need for 1,200 new homes per year (2024-2039). Strong demand for affordable housing (45% of total need). Need for family housing (3+ beds) particularly acute in zones 2-3. Average household size declining to 2.1 persons. Significant backlog of housing need from previous periods.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Core evidence for Local Plan housing policies. Updates 2021 SHMA.",
        "versions": [
            {"version": 1, "year": 2021, "status": "superseded"},
            {"version": 2, "year": 2023, "status": "draft"},
            {"version": 3, "year": 2024, "status": "adopted"}
        ],
        "policy_links": [1, 2, 3]  # H1, H2, H3
    },
    {
        "title": "Camden Housing & Economic Needs Assessment 2023",
        "type": "HENA",
        "topic_tags": ["housing", "economy"],
        "geographic_scope": "Camden Council",
        "author": "Turley Associates",
        "publisher": "Camden Council",
        "year": 2023,
        "source_type": "cached_url",
        "key_findings": "Housing need: 900 homes/year. Economic growth forecast: 15,000 new jobs (2023-2038). Office space demand: 85,000 sqm. Industrial land to be protected (minimum 20ha). Retail floorspace stable, shift to convenience.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Joint housing and employment evidence base",
        "policy_links": [1, 2]
    },
    {
        "title": "Islington Strategic Housing Market Assessment 2022",
        "type": "SHMA",
        "topic_tags": ["housing"],
        "geographic_scope": "Islington Council",
        "author": "Opinion Research Services",
        "publisher": "Islington Council",
        "year": 2022,
        "source_type": "upload",
        "key_findings": "Housing need: 1,480 homes/year. 52% affordable requirement (40% social rent, 60% intermediate). Student housing demand: 1,200 bed spaces over plan period. Purpose-built shared living need minimal.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Informs affordable housing policy",
        "policy_links": [2, 3]
    },
    {
        "title": "Southwark Affordable Housing Viability Study 2024",
        "type": "Viability Study",
        "topic_tags": ["housing", "economy"],
        "geographic_scope": "Southwark Council",
        "author": "BNP Paribas Real Estate",
        "publisher": "Southwark Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "40% affordable housing viable on brownfield sites in zones 1-2. 35% viable elsewhere. Industrial land conversions can support 25% affordable. Grant funding critical for social rent delivery. Build-to-rent can deliver affordable private rent at 20% discount.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Underpins affordable housing policy targets",
        "policy_links": [2]
    },
    {
        "title": "Hackney Housing Delivery Study 2023",
        "type": "Housing Delivery Study",
        "topic_tags": ["housing", "economy"],
        "geographic_scope": "Hackney Council",
        "author": "Savills",
        "publisher": "Hackney Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "Historic delivery: 750 homes/year (2018-2023). Pipeline: 12,000 homes with planning permission. Delivery rate expected 850/year (2024-2029). Build-to-rent comprises 30% of pipeline. SME builders account for 15% of delivery.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "5-year land supply evidence",
        "policy_links": [1]
    },
    {
        "title": "Tower Hamlets Specialist Housing Needs Assessment 2024",
        "type": "Specialist Housing Assessment",
        "topic_tags": ["housing", "social"],
        "geographic_scope": "Tower Hamlets Council",
        "author": "Housing LIN",
        "publisher": "Tower Hamlets Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Older persons housing need: 2,500 units over 15 years (mix of sheltered, extra care, care homes). Supported housing need: 800 units for adults with disabilities. Student housing demand: 3,000 bed spaces. Co-living minimal demand.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Specialist and supported housing evidence",
        "policy_links": [3]
    },
    {
        "title": "Brent Gypsy & Traveller Accommodation Assessment 2022",
        "type": "GTAA",
        "topic_tags": ["housing", "social"],
        "geographic_scope": "Brent Council",
        "author": "ORS",
        "publisher": "Brent Council",
        "year": 2022,
        "source_type": "upload",
        "key_findings": "Need for 8 additional pitches (2022-2037). Existing site at Bashley Road at capacity (12 pitches). Travelling Showpeople need: 3 plots. Transit site provision adequate (London-wide).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Meets PPTS requirements",
        "policy_links": []
    },
    {
        "title": "Lambeth Housing Market Analysis 2023",
        "type": "Housing Market Analysis",
        "topic_tags": ["housing", "economy"],
        "geographic_scope": "Lambeth Council",
        "author": "Hometrack",
        "publisher": "Lambeth Council",
        "year": 2023,
        "source_type": "cached_url",
        "key_findings": "Median house price: £575,000 (2023). Price growth: 4.2% annual average (2018-2023). Affordability ratio: 14.2x median earnings. Private rental sector: 35% of households. Build-to-rent rents 15-20% below market.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Market context for housing policies",
        "policy_links": [1, 2]
    },
    {
        "title": "Greenwich First Homes Viability Assessment 2024",
        "type": "Viability Study",
        "topic_tags": ["housing", "economy"],
        "geographic_scope": "Greenwich Council",
        "author": "Three Dragons",
        "publisher": "Greenwich Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "First Homes at 25% discount viable as part of affordable housing mix (max 25% of affordable). Does not displace social rent provision. Price caps: £420,000 (1-bed), £525,000 (2-bed), £630,000 (3-bed).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "First Homes policy evidence",
        "policy_links": [2]
    },
    {
        "title": "Ealing Housing Space Standards Review 2023",
        "type": "Space Standards Evidence",
        "topic_tags": ["housing", "design"],
        "geographic_scope": "Ealing Council",
        "author": "Design Council",
        "publisher": "Ealing Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "NDSS viable across all typologies without impacting affordable housing delivery. Viability impact: 2-3% of GDV. Quality improvements justify cost. Existing stock analysis: 60% of flats below NDSS.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Justifies NDSS policy requirement",
        "policy_links": [3]
    },
    
    # ========== ECONOMY & EMPLOYMENT (8 items) ==========
    {
        "title": "Westminster Employment Land Review 2024",
        "type": "Employment Land Review",
        "topic_tags": ["economy", "employment"],
        "geographic_scope": "Westminster City Council",
        "author": "Nathaniel Lichfield & Partners",
        "publisher": "Westminster City Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Office demand: 120,000 sqm (2024-2040). Central Activities Zone office stock: 2.8m sqm (maintain). Industrial land: 15ha to retain (light industrial, creative industries). Co-working space growth: 25% of office demand. Hybrid working impact: -15% space per worker.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Core employment evidence",
        "policy_links": []
    },
    {
        "title": "Camden Employment Floorspace Demand Study 2023",
        "type": "Employment Study",
        "topic_tags": ["economy", "employment"],
        "geographic_scope": "Camden Council",
        "author": "Regeneris Consulting",
        "publisher": "Camden Council",
        "year": 2023,
        "source_type": "cached_url",
        "key_findings": "Office demand: 65,000 sqm. Knowledge Quarter growth sector: life sciences, AI, creative industries. Industrial land: 18ha minimum (protect existing). Workspace for SMEs: 15,000 sqm needed. Affordable workspace: 10% of major office schemes.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Employment policies evidence base",
        "policy_links": []
    },
    {
        "title": "Islington Retail & Leisure Needs Assessment 2023",
        "type": "Retail Study",
        "topic_tags": ["economy", "retail"],
        "geographic_scope": "Islington Council",
        "author": "Cushman & Wakefield",
        "publisher": "Islington Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "Comparison retail floorspace: surplus 5,000 sqm (online impact). Convenience retail: capacity for 3,500 sqm (population growth). Town centre boundaries review: reduce by 10% (consolidate). Leisure demand: 2,500 sqm (F&B, gyms, entertainment).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Town centre and retail policies",
        "policy_links": []
    },
    {
        "title": "City of London Office Market Dynamics Study 2024",
        "type": "Office Market Study",
        "topic_tags": ["economy", "employment"],
        "geographic_scope": "City of London Corporation",
        "author": "Lambert Smith Hampton",
        "publisher": "City of London Corporation",
        "year": 2024,
        "source_type": "cached_url",
        "key_findings": "Office stock: 12.5m sqm. Grade A demand: 180,000 sqm/year. ESG refurbishment: 40% of stock needs upgrading. Financial services: 55% of demand. Tech sector: 20% and growing. Hybrid working: 60% occupancy (stabilising).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "CAZ office strategy evidence",
        "policy_links": []
    },
    {
        "title": "Southwark Town Centre Health Checks 2024",
        "type": "Town Centre Study",
        "topic_tags": ["economy", "retail", "social"],
        "geographic_scope": "Southwark Council",
        "author": "WYG",
        "publisher": "Southwark Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Peckham: healthy (vacancy 8%). Old Kent Road: opportunity area (19% vacancy). Canada Water: regenerating well. Camberwell: challenged (15% vacancy, parking issues). Walworth Road: stable (local centre role).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Town centre hierarchy and policies",
        "policy_links": []
    },
    {
        "title": "Hackney Creative Enterprise Zone Strategy 2023",
        "type": "Economic Strategy",
        "topic_tags": ["economy", "culture", "employment"],
        "geographic_scope": "Hackney Council",
        "author": "Hackney Council / GLA",
        "publisher": "Hackney Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "Mare Street CEZ: protect 25,000 sqm workspace. Affordable workspace: 30% of developments. Creative sector jobs: 8,000 (protect and grow). Artist studios: 150 units needed. Meanwhile uses for vacant sites.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Creative industries policy support",
        "policy_links": []
    },
    {
        "title": "Tower Hamlets Canary Wharf Economic Impact Study 2024",
        "type": "Economic Study",
        "topic_tags": ["economy", "employment", "transport"],
        "geographic_scope": "Tower Hamlets Council",
        "author": "Volterra",
        "publisher": "Tower Hamlets Council",
        "year": 2024,
        "source_type": "cached_url",
        "key_findings": "Employment: 120,000 jobs (2024). Office stock: 1.5m sqm. Residential population: 15,000 (planned growth to 25,000). Retail & leisure: 30,000 sqm F&B, entertainment. Transport capacity: Elizabeth Line easing congestion.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Canary Wharf opportunity area",
        "policy_links": []
    },
    {
        "title": "Lewisham Local Industrial Strategy 2023",
        "type": "Industrial Strategy",
        "topic_tags": ["economy", "employment", "environment"],
        "geographic_scope": "Lewisham Council",
        "author": "AECOM",
        "publisher": "Lewisham Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "Strategic Industrial Locations: 45ha (no net loss). Locally Significant Industrial Sites: 20ha. Modern industrial space needed: 30,000 sqm (low-carbon, multi-storey). Circular economy businesses: grow from 15 to 50. Last-mile logistics: plan for consolidation centres.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Industrial land policies",
        "policy_links": []
    },
    
    # ========== ENVIRONMENT & INFRASTRUCTURE (12 items) ==========
    {
        "title": "London Plan Strategic Flood Risk Assessment 2023",
        "type": "SFRA",
        "topic_tags": ["environment", "climate", "infrastructure"],
        "geographic_scope": "Greater London Authority",
        "author": "JBA Consulting",
        "publisher": "Greater London Authority",
        "year": 2023,
        "source_type": "cached_url",
        "key_findings": "15% of London at significant flood risk (Zones 2 & 3). Thames Barrier protected to 2070 (2100 with upgrades). Surface water flooding: 480,000 properties at risk. Climate change: +20% flood zones by 2050. Sequential test: apply to all sites. SuDS mandatory for major developments.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Supersedes 2019 SFRA. Critical for flood risk policy.",
        "versions": [
            {"version": 1, "year": 2019, "status": "superseded"},
            {"version": 2, "year": 2023, "status": "adopted"}
        ],
        "policy_links": []
    },
    {
        "title": "Westminster Level 2 Strategic Flood Risk Assessment 2024",
        "type": "SFRA Level 2",
        "topic_tags": ["environment", "climate"],
        "geographic_scope": "Westminster City Council",
        "author": "JBA Consulting",
        "publisher": "Westminster City Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "10 allocation sites in Flood Zone 2/3 (all pass Exception Test with mitigation). Residual risk from Thames Barrier failure: plan for safe refuge. Basements: groundwater flooding risk (policy controls needed). SuDS: limited space, green roofs primary solution.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Site-specific flood risk evidence",
        "policy_links": []
    },
    {
        "title": "Camden Climate Action Plan Evidence Base 2024",
        "type": "Climate Strategy",
        "topic_tags": ["climate", "environment", "energy"],
        "geographic_scope": "Camden Council",
        "author": "Anthesis",
        "publisher": "Camden Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Borough carbon emissions: 850ktCO2e (2023). 2030 target: 50% reduction. 2040 target: net zero. Buildings: 65% of emissions. Transport: 25%. New developments: net zero carbon from 2025. Retrofitting: 40,000 homes by 2030. Renewable energy: 15MW solar potential.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Climate emergency policies evidence",
        "policy_links": []
    },
    {
        "title": "Islington Biodiversity Net Gain Baseline Study 2024",
        "type": "Biodiversity Assessment",
        "topic_tags": ["environment", "biodiversity"],
        "geographic_scope": "Islington Council",
        "author": "The Ecology Consultancy",
        "publisher": "Islington Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Urban habitat units baseline: 12,500 units. BNG achievable on-site: 75% of major schemes (10%+ gain). Off-site provision: 15ha strategic sites identified. Biodiversity Opportunity Areas: 8 sites. Priority habitats: woodland (12ha), wetland (3ha), brownfield (20ha).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "BNG policy compliance evidence",
        "policy_links": []
    },
    {
        "title": "Southwark Air Quality Action Plan Evidence 2023",
        "type": "Air Quality Assessment",
        "topic_tags": ["environment", "health", "transport"],
        "geographic_scope": "Southwark Council",
        "author": "Ricardo Energy & Environment",
        "publisher": "Southwark Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "NO2: 85% of borough meets objectives (95% by 2025). PM2.5: exceedances in 5 locations (traffic hotspots). Air Quality Focus Areas: Old Kent Road, Elephant & Castle. Development impacts: air quality neutral required. Ultra Low Emission Zone: 60% reduction in roadside NO2.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Air quality policies support",
        "policy_links": []
    },
    {
        "title": "Hackney Contaminated Land Strategy 2023",
        "type": "Contaminated Land Assessment",
        "topic_tags": ["environment", "health"],
        "geographic_scope": "Hackney Council",
        "author": "Soiltechnics",
        "publisher": "Hackney Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "Historical contamination sites: 450 (35% remediated). Priority sites: 18 (former gasworks, industrial). Development requirement: Phase 1 desk study mandatory. Groundwater contamination: 8 sites (monitoring ongoing).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Land contamination policies",
        "policy_links": []
    },
    {
        "title": "Tower Hamlets Noise Assessment & Mitigation Study 2024",
        "type": "Noise Assessment",
        "topic_tags": ["environment", "health", "transport"],
        "geographic_scope": "Tower Hamlets Council",
        "author": "24 Acoustics",
        "publisher": "Tower Hamlets Council",
        "year": 2024,
        "source_type": "cached_url",
        "key_findings": "Noise Important Areas: 25 locations (mainly A-roads, Overground). Residential developments: acoustic design standards needed (internal 30dB). Agent of Change principle: protect existing music venues (12 venues). Quiet areas: 5 parks designated.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Noise policy and agent of change",
        "policy_links": []
    },
    {
        "title": "Brent Water Cycle Study 2023",
        "type": "Water Cycle Study",
        "topic_tags": ["infrastructure", "environment", "climate"],
        "geographic_scope": "Brent Council",
        "author": "AECOM",
        "publisher": "Brent Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "Water supply: sufficient capacity (Thames Water). Wastewater: Mogden WWTW at 95% capacity (upgrades planned 2026). Water efficiency: 105 l/p/d target achievable. SuDS: 50% surface water attenuation required. River Brent restoration: 3km priority reach.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Water infrastructure evidence",
        "policy_links": []
    },
    {
        "title": "Lambeth Urban Greening Factor Evidence Base 2024",
        "type": "Urban Greening Study",
        "topic_tags": ["environment", "climate", "design"],
        "geographic_scope": "Lambeth Council",
        "author": "TEP",
        "publisher": "Lambeth Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Existing UGF: 0.25 (borough average). Target UGF: 0.4 (residential), 0.3 (commercial). Achievable on 90% of major sites. Green roofs: 120,000 sqm potential. Street trees: 8,000 new trees target (2024-2034). Cooling effect: -2°C in urban heat island.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Urban greening policy calibration",
        "policy_links": []
    },
    {
        "title": "Greenwich Thames Estuary Habitat Creation Study 2023",
        "type": "Habitat Creation Study",
        "topic_tags": ["environment", "biodiversity", "climate"],
        "geographic_scope": "Greenwich Council",
        "author": "Environment Agency / GLA",
        "publisher": "Greenwich Council",
        "year": 2023,
        "source_type": "cached_url",
        "key_findings": "Intertidal habitat creation: 15ha potential (Crossness to Thamesmead). Saltmarsh restoration: 8ha. Reedbeds: 4ha. Carbon sequestration: 120 tCO2e/year. Biodiversity units: +8,500 units. Flood risk benefits: natural flood management.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Thames Estuary policies support",
        "policy_links": []
    },
    {
        "title": "Ealing Renewable Energy & Low Carbon Study 2024",
        "type": "Renewable Energy Study",
        "topic_tags": ["energy", "climate", "environment"],
        "geographic_scope": "Ealing Council",
        "author": "AECOM",
        "publisher": "Ealing Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Solar PV potential: 45MW (commercial roofs 25MW, residential 20MW). Heat networks: 8 opportunity areas (12,000 homes). Ground source heat pumps: viable in 40% of borough. Wind: not viable (urban context). Biomass: limited (air quality concerns).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Renewable energy policy evidence",
        "policy_links": []
    },
    {
        "title": "Haringey Digital Connectivity Infrastructure Study 2023",
        "type": "Digital Infrastructure Study",
        "topic_tags": ["infrastructure", "economy"],
        "geographic_scope": "Haringey Council",
        "author": "Point Topic",
        "publisher": "Haringey Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "Full fibre coverage: 78% (target 100% by 2026). 5G coverage: 65% outdoors. Mobile not-spots: 8 locations. Ducting: require in major schemes. Smart city infrastructure: 200 sensor locations planned.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Digital infrastructure policies",
        "policy_links": []
    },
    
    # ========== TRANSPORT (3 items) ==========
    {
        "title": "Camden Transport Strategy Evidence Base 2022",
        "type": "Transport Assessment",
        "topic_tags": ["transport", "infrastructure", "climate"],
        "geographic_scope": "Camden Council",
        "author": "Transport for London",
        "publisher": "Camden Council",
        "year": 2022,
        "source_type": "upload",
        "key_findings": "Public transport accessibility (PTAL): ranges from 1a (Gospel Oak) to 6b (Euston, King's Cross). Northern Line at capacity during AM peak (upgrade needed post-2030). Active travel target: 30% of trips by 2030. Car ownership declining: 32% of households (2021). Cycle network: 85km (target 120km by 2030).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Supports sustainable transport policies",
        "policy_links": []
    },
    {
        "title": "Westminster Parking Standards Review 2024",
        "type": "Parking Study",
        "topic_tags": ["transport", "design"],
        "geographic_scope": "Westminster City Council",
        "author": "Steer",
        "publisher": "Westminster City Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Car parking: car-free development appropriate in PTAL 4-6 (85% of borough). Blue Badge parking: 3% of units minimum. Cycle parking: 1.5 spaces per flat (London Plan), 1 per 75sqm office. EV charging: 20% active, 80% passive provision. Car club bays: 150 locations across borough.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Parking policy standards evidence",
        "policy_links": []
    },
    {
        "title": "Islington Healthy Streets Assessment 2023",
        "type": "Healthy Streets Study",
        "topic_tags": ["transport", "health", "design"],
        "geographic_scope": "Islington Council",
        "author": "TfL / Islington Council",
        "publisher": "Islington Council",
        "year": 2023,
        "source_type": "cached_url",
        "key_findings": "Healthy Streets score: 58/100 (borough average). Priority streets: 45 locations for improvement. School Streets: 60 schools (expand to 75). Low Traffic Neighbourhoods: 12 areas (reduce through-traffic 60%). Walking: 35% of trips (target 40% by 2030).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Healthy streets and active travel",
        "policy_links": []
    },
    
    # ========== SPATIAL & LAND (4 items) ==========
    {
        "title": "Westminster Strategic Housing & Employment Land Availability Assessment 2024",
        "type": "SHELAA",
        "topic_tags": ["housing", "economy", "environment"],
        "geographic_scope": "Westminster City Council",
        "author": "Arup",
        "publisher": "Westminster City Council",
        "year": 2024,
        "source_type": "cached_url",
        "key_findings": "Housing capacity: 18,000 homes on identified sites (2024-2040). 55% on brownfield land. 30% on office-to-resi conversions. Major sites: Paddington Opportunity Area (4,500 homes), Victoria (2,000 homes). Employment: 180,000 sqm office capacity. Delivery: 1,125 homes/year achievable.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Annual update due Q4 2025. Core evidence for site allocations.",
        "versions": [
            {"version": 1, "year": 2023, "status": "draft"},
            {"version": 2, "year": 2024, "status": "adopted"}
        ],
        "policy_links": [1]
    },
    {
        "title": "Camden Brownfield Register 2024",
        "type": "Brownfield Register",
        "topic_tags": ["housing", "environment"],
        "geographic_scope": "Camden Council",
        "author": "Camden Council",
        "publisher": "Camden Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Brownfield sites: 42 sites (25ha total). Housing capacity: 3,800 homes. Part 2 (permission in principle): 5 sites (450 homes). Constraints: 18 sites in flood zones, 12 with contamination. Delivery timeframe: 65% deliverable 0-5 years.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Published annually (statutory requirement)",
        "policy_links": [1]
    },
    {
        "title": "Islington Green Belt & MOL Review 2023",
        "type": "Green Belt Review",
        "topic_tags": ["environment", "housing"],
        "geographic_scope": "Islington Council",
        "author": "LUC",
        "publisher": "Islington Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "Metropolitan Open Land: 85ha (no exceptional circumstances to alter boundaries). Playing fields: 15 sites (protected, Sport England). Parks & gardens: 45 sites (Local Plan designation). Biodiversity sites: SINC network 120ha. No Green Belt in borough.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Green space protection policies",
        "policy_links": []
    },
    {
        "title": "Southwark Settlement Hierarchy & Density Study 2024",
        "type": "Settlement Hierarchy Study",
        "topic_tags": ["design", "housing"],
        "geographic_scope": "Southwark Council",
        "author": "PTE",
        "publisher": "Southwark Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Town centres: 5 (Major: Peckham, Canada Water. District: Camberwell, Old Kent Road, Walworth). Density zones: Central (650+ hr/ha), Urban (240-650 hr/ha), Suburban (<240 hr/ha). PTAL correlates with density capacity. Design-led approach for tall buildings (>30m).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Density and tall buildings policy",
        "policy_links": []
    },
    
    # ========== HERITAGE & DESIGN (2 items) ==========
    {
        "title": "City of London Heritage & Tall Buildings Study 2020",
        "type": "Heritage Assessment",
        "topic_tags": ["heritage", "design", "environment"],
        "geographic_scope": "City of London Corporation",
        "author": "Historic England / City of London",
        "publisher": "City of London Corporation",
        "year": 2020,
        "source_type": "upload",
        "key_findings": "Protected views framework: 15 key vistas (St Paul's Cathedral primary). Eastern Cluster: suitable for tall buildings up to 300m (10 consented). Conservation areas: 25 (40% of City area). Scheduled monuments: 46. Heritage at risk: 8 buildings. Character areas: 5 distinct types.",
        "status": "adopted",
        "reliability_flags": {"stale": True},
        "notes": "Pre-dates recent tall building applications. Update planned 2025.",
        "policy_links": []
    },
    {
        "title": "Camden Design Code Evidence Base 2024",
        "type": "Design Code Evidence",
        "topic_tags": ["design", "housing", "heritage"],
        "geographic_scope": "Camden Council",
        "author": "CGMS / Camden Council",
        "publisher": "Camden Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Character areas: 12 types (Georgian, Victorian, Modernist, Industrial). Height parameters: 3-5 storeys prevailing, up to 25 storeys at King's Cross, Euston. Materials palette: London stock brick, red/brown brick, glazed brick. Frontage: 60% active minimum. Street trees: 10m spacing target.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Area design codes support",
        "policy_links": []
    },
    
    # ========== SOCIAL & COMMUNITY (5 items) ==========
    {
        "title": "Tower Hamlets Health Impact Assessment Methodology 2023",
        "type": "Health Impact Assessment",
        "topic_tags": ["health", "social"],
        "geographic_scope": "Tower Hamlets Council",
        "author": "Public Health England / HUDU",
        "publisher": "Tower Hamlets Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "HIA required for major developments (150+ homes, 5,000+ sqm non-resi). Health indicators: access to healthcare (800m), open space (400m), active travel, noise, air quality. Priority health inequalities: reduce life expectancy gap (7 years variance across borough).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Health policies support",
        "policy_links": []
    },
    {
        "title": "Hackney Education Capacity Assessment 2024",
        "type": "Education Capacity Study",
        "topic_tags": ["social", "infrastructure"],
        "geographic_scope": "Hackney Council",
        "author": "Hackney Education / GLA",
        "publisher": "Hackney Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Primary schools: surplus 8% capacity (falling rolls). Secondary schools: 95% capacity (growth pressure from 2027). New school needed: 1 secondary (2029). SEN places: 120 additional places needed. Child yield: 25 primary per 100 homes, 12 secondary.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Education infrastructure planning",
        "policy_links": []
    },
    {
        "title": "Lambeth Open Space & Recreation Study 2023",
        "type": "Open Space Study",
        "topic_tags": ["social", "environment", "health"],
        "geographic_scope": "Lambeth Council",
        "author": "Knight Kavanagh & Page",
        "publisher": "Lambeth Council",
        "year": 2023,
        "source_type": "cached_url",
        "key_findings": "Open space: 320ha (1.2ha per 1,000 population). Access standards: 400m to local park (85% coverage). Deficiency: 6 wards below standard. Playing pitches: shortfall of 8 adult football, 4 rugby. Playgrounds: 80 sites (15 need refurbishment).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Open space policies and standards",
        "policy_links": []
    },
    {
        "title": "Greenwich Cultural Infrastructure Audit 2024",
        "type": "Cultural Infrastructure Study",
        "topic_tags": ["culture", "social", "economy"],
        "geographic_scope": "Greenwich Council",
        "author": "BOP Consulting",
        "publisher": "Greenwich Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Cultural venues: 45 (5 strategic: O2, National Maritime Museum). Artist studios: 250 spaces (35% affordable). Creative industries: 4,500 jobs. Music venues: 8 (protect under Agent of Change). Libraries: 12 branches (1 per 25,000 residents).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Cultural policies evidence",
        "policy_links": []
    },
    {
        "title": "Ealing Equality Impact Assessment 2023",
        "type": "Equality Impact Assessment",
        "topic_tags": ["social", "housing", "economy"],
        "geographic_scope": "Ealing Council",
        "author": "Ealing Council Policy Team",
        "publisher": "Ealing Council",
        "year": 2023,
        "source_type": "upload",
        "key_findings": "Protected characteristics analysis: positive impact on housing affordability (disability, age, families). Neutral on transport (PTAL coverage equitable). Mitigation needed: Gypsy & Traveller provision, accessible housing (M4(3) 10% policy). Engagement: 45% BAME respondents, 52% female.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "EqIA for Local Plan",
        "policy_links": []
    },
    
    # ========== VIABILITY & CIL (2 items) ==========
    {
        "title": "Islington Whole Plan Viability Assessment 2021",
        "type": "Viability Study",
        "topic_tags": ["housing", "economy", "infrastructure"],
        "geographic_scope": "Islington Council",
        "author": "BNP Paribas Real Estate",
        "publisher": "Islington Council",
        "year": 2021,
        "source_type": "upload",
        "key_findings": "35% affordable housing viable in high value areas (Canonbury, Highbury), 25% elsewhere. CIL rates supportable up to £200/sqm in most areas. Infrastructure funding gap: £150m over plan period. Policy cost impacts: NDSS (+2%), carbon zero (+3%), BNG (+1%).",
        "status": "adopted",
        "reliability_flags": {"stale": True},
        "notes": "May need updating due to post-2021 market changes. Underpins affordable housing targets.",
        "policy_links": [2]
    },
    {
        "title": "Westminster CIL Infrastructure Funding Statement 2024",
        "type": "CIL Funding Statement",
        "topic_tags": ["infrastructure", "economy"],
        "geographic_scope": "Westminster City Council",
        "author": "Westminster City Council",
        "publisher": "Westminster City Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "CIL income: £18.5m (2023/24). Allocated to: transport (40%), education (25%), health (15%), open space (10%), community (10%). S106: £12m (affordable housing, site-specific). Infrastructure Delivery Plan: £420m total cost (CIL covers 25%).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Annual publication (statutory). Infrastructure planning.",
        "policy_links": []
    },
]

def seed_evidence():
    """Insert comprehensive evidence into database with versions and policy links"""
    try:
        import psycopg
        conn = psycopg.connect("postgresql://tpa:tpa@127.0.0.1:5432/tpa")
    except ImportError:
        print("❌ psycopg not installed. Install with: pip install psycopg[binary]")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Could not connect to database: {e}")
        sys.exit(1)
    
    try:
        with conn.cursor() as cur:
            # First, get existing policy IDs to link to
            cur.execute("SELECT id FROM policy ORDER BY id LIMIT 10")
            policy_ids = [row[0] for row in cur.fetchall()]
            
            if not policy_ids:
                print("⚠️  Warning: No policies found in database. Policy links will be skipped.")
            
            evidence_count = 0
            version_count = 0
            link_count = 0
            
            for item in SAMPLE_EVIDENCE:
                # Extract versions and policy_links before inserting
                versions = item.pop("versions", [{"version": 1, "status": "adopted"}])
                policy_links = item.pop("policy_links", [])
                
                # Convert reliability_flags dict to JSON string
                reliability_flags_json = json.dumps(item["reliability_flags"])
                
                # Insert evidence item
                cur.execute("""
                    INSERT INTO evidence (
                        title, type, topic_tags, geographic_scope,
                        author, publisher, year, source_type,
                        key_findings, status, reliability_flags, notes,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s::jsonb, %s,
                        NOW(), NOW()
                    )
                    RETURNING id
                """, (
                    item["title"], item["type"], item["topic_tags"], item["geographic_scope"],
                    item["author"], item["publisher"], item["year"], item["source_type"],
                    item["key_findings"], item["status"], reliability_flags_json, item["notes"]
                ))
                
                evidence_id = cur.fetchone()[0]
                evidence_count += 1
                
                # Create versions
                for v in versions:
                    version_num = v.get("version", 1)
                    version_year = v.get("year", item["year"])
                    version_status = v.get("status", "adopted")
                    
                    cur.execute("""
                        INSERT INTO evidence_version (
                            evidence_id, version_number, cas_hash,
                            fetched_at, robots_allowed, created_at
                        ) VALUES (
                            %s, %s, %s, NOW(), TRUE, NOW()
                        )
                    """, (
                        evidence_id,
                        version_num,
                        f"sha256_{evidence_id}_v{version_num}_{version_year}"
                    ))
                    version_count += 1
                
                # Create policy links
                for policy_idx in policy_links:
                    if policy_idx < len(policy_ids):
                        policy_id = policy_ids[policy_idx]
                        
                        # Vary strength based on position
                        if policy_idx == policy_links[0]:
                            strength = "core"
                        elif len(policy_links) <= 2:
                            strength = "supporting"
                        else:
                            strength = "tangential" if policy_idx > 2 else "supporting"
                        
                        rationale = f"Evidence underpins policy targets and assumptions"
                        
                        cur.execute("""
                            INSERT INTO evidence_policy_link (
                                evidence_id, policy_id, rationale, strength, created_at
                            ) VALUES (
                                %s, %s, %s, %s, NOW()
                            )
                            ON CONFLICT (evidence_id, policy_id) DO NOTHING
                        """, (evidence_id, policy_id, rationale, strength))
                        link_count += 1
                
                print(f"✓ Added: {item['title'][:60]}... ({len(versions)} versions)")
        
        conn.commit()
        print(f"\n✅ Seeded {evidence_count} evidence items")
        print(f"   └─ {version_count} versions created")
        print(f"   └─ {link_count} policy links created")
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    print("🌱 Seeding comprehensive evidence database...\n")
    print(f"   Evidence types: SHMA, HENA, SFRA, Viability, SHELAA, Transport,")
    print(f"   Employment, Retail, Heritage, Social, Infrastructure, Climate\n")
    try:
        seed_evidence()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

