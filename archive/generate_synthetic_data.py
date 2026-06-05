"""
Synthetic Telecom Incidents CSV Generator
Generates 1300 rows of realistic telecom incident data.
"""

import random
import csv
import os
from datetime import datetime, timedelta

random.seed(42)

# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "telecom_incidents.csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Configuration ─────────────────────────────────────────────────────────────
NETWORK_REGIONS = [
    "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Singapore", "London", "Dubai", "New York", "Tokyo",
    "Frankfurt", "Sydney", "Toronto",
]

TECHNOLOGY_TYPES = [
    "5G-NR", "4G-LTE", "3G-UMTS", "Fiber-Optic",
    "MPLS-Core", "RAN", "IP-Core", "Microwave-Backhaul", "Cloud-RAN",
]

SEVERITY_CHOICES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
SEVERITY_WEIGHTS = [0.15, 0.25, 0.40, 0.20]

VENDORS = ["Ericsson", "Nokia", "Huawei", "Cisco", "Juniper"]
VENDOR_WEIGHTS = [0.25, 0.22, 0.28, 0.15, 0.10]

SERVICE_IMPACTS = [
    "Voice calls affected",
    "Data sessions degraded",
    "SMS delivery delayed",
    "Emergency services impacted",
    "Enterprise VPN disrupted",
    "IoT connectivity lost",
    "Mobile broadband throughput reduced",
    "Roaming services unavailable",
    "Video streaming interrupted",
    "Fixed broadband users affected",
    "Cloud-hosted applications unreachable",
    "Inter-site backhaul degraded",
    "Wholesale transit impacted",
    "Public safety network degraded",
    "Financial transaction services disrupted",
]

# ── Start/End timestamps ───────────────────────────────────────────────────────
START_TS = datetime(2024, 1, 1, 0, 0, 0)
END_TS   = datetime(2026, 6, 1, 23, 59, 59)
TS_RANGE_SECS = int((END_TS - START_TS).total_seconds())

# ── Incident templates keyed by technology type ───────────────────────────────
# Each entry: (description_template, resolution_template)

TEMPLATES = {
    "5G-NR": [
        (
            "5G NR gNodeB {vendor} lost synchronization with primary GNSS clock source at site {site}. Timing error exceeded 1.5 µs threshold causing downstream cell outage.",
            "Replaced faulty GNSS antenna cable and re-synchronized gNodeB to backup IEEE 1588 PTP grandmaster. Verified synchronization accuracy within ±100 ns. Service restored.",
        ),
        (
            "5G NR massive MIMO antenna unit on {vendor} gNodeB reported power amplifier fault at {site}. Beam-forming capability reduced by 60%, causing significant coverage degradation.",
            "Dispatched field engineer to replace defective RRU power amplifier module. Updated antenna calibration parameters and validated EIRP levels post-repair.",
        ),
        (
            "F1 interface between {vendor} gNodeB and Central Unit (CU) dropped at {site} due to transport network packet loss exceeding 0.5%. UEs unable to complete RRC connection setup.",
            "Identified faulty SFP transceiver on fronthaul switch. Replaced SFP module and re-established F1-C and F1-U interface. Confirmed PDCP/RLC layer recovery.",
        ),
        (
            "5G NR {vendor} gNodeB experienced Xn handover failures with neighboring cells at {site}. Inter-gNB mobility success rate dropped to 42% from baseline 98%.",
            "Reset Xn interface and re-applied neighbor relation configuration. Tuned A3 event offset parameters and re-synchronized ANR tables. Mobility KPIs restored to 97%.",
        ),
        (
            "NG interface between {vendor} gNodeB and AMF core became unstable at {site}. NGAP signaling failures caused mass UE deregistration affecting {count} subscribers.",
            "Restarted SCTP associations on N2 interface. Restored AMF connectivity and triggered UE re-registration. Verified N2 and N3 interface stability over 30-minute observation window.",
        ),
        (
            "5G NR uplink interference detected on n78 band at {site}. SINR degraded to -3 dB, causing throughput reduction of 75% for connected UEs on {vendor} gNodeB.",
            "Conducted interference hunting using spectrum analyzer. Identified rogue transmission source. Coordinated with regulatory authority for interference mitigation. Applied notch filter on affected PRBs.",
        ),
        (
            "{vendor} gNodeB CU-CP software exception caused unexpected process restart at {site}. All active PDU sessions dropped during 4-minute recovery window.",
            "Reviewed core dump and identified memory leak in NAS message parser. Applied vendor hotfix patch and restarted CU-CP process. Enhanced monitoring threshold for process memory utilization.",
        ),
        (
            "5G NR cell capacity alarm triggered on {vendor} gNodeB at {site}. PRB utilization sustained above 95% for 45 minutes causing packet scheduler congestion.",
            "Enabled carrier aggregation on n41+n78 bands. Offloaded heavy users to adjacent underutilized cell. Implemented traffic shaping policy and scheduled capacity expansion.",
        ),
        (
            "Fronthaul eCPRI link between {vendor} RRU and DU lost at {site}. L1 processing failure caused complete cell blackout for {count} active UEs.",
            "Replaced degraded fiber patch cord on fronthaul ring. Verified eCPRI frame alignment and L1 timing. Re-established DU-RU connection and confirmed cell availability.",
        ),
        (
            "5G NR {vendor} DU reported clock holdover failure at {site}. SyncE signal quality degraded, triggering EEC holdover mode. Cell downgrade to LTE fallback initiated.",
            "Restored primary SyncE source from upstream PTN node. Verified ITU-T G.8262 compliance. Upgraded DU firmware to address clock tracking algorithm defect.",
        ),
        (
            "5G SA core network slice configuration mismatch on {vendor} gNodeB at {site}. URLLC slice latency exceeded 5 ms SLA causing industrial IoT application failures.",
            "Corrected network slice subnet management (NSSM) configuration. Re-applied QoS flow to DRB mapping parameters. Validated end-to-end slice latency < 1 ms.",
        ),
        (
            "{vendor} gNodeB reported excessive CRC errors on PDSCH channel at {site}. MCS adaptation reduced to QPSK causing 80% throughput degradation.",
            "Identified loose connector on antenna feeder port. Re-seated N-type connector and applied weatherproofing. BLER reduced to 0.1% and MCS recovered to 256QAM.",
        ),
        (
            "5G NR {vendor} O-RU reported overtemperature alarm at {site}. Thermal protection activated, reducing transmit power by 50% to prevent hardware damage.",
            "Cleared blocked ventilation grilles and replaced faulty cooling fan unit. Ambient temperature normalized. Transmit power restored to configured maximum after 20-minute cooling period.",
        ),
        (
            "AMF selection failure for {vendor} gNodeB at {site}. NRF service discovery returned stale AMF endpoints causing 100% NG setup failure rate.",
            "Refreshed NRF registration for AMF instances. Cleared stale NF profile cache and triggered re-discovery. Verified AMF load distribution across pool.",
        ),
        (
            "5G NR beam management failure on {vendor} gNodeB at {site}. SSB beam sweep not detected by 35% of UEs causing persistent RLF in beam-limited coverage areas.",
            "Re-calibrated SSB transmission periodicity and beam sweep pattern. Adjusted SS-RSRP threshold for beam failure detection. CSI-RS configuration optimized for beam tracking.",
        ),
        (
            "UPF user-plane path failure caused 5G data session drops on {vendor} gNodeB at {site}. GTP-U tunnel establishment failures reached 100% for 12 minutes.",
            "Restarted UPF pod in Kubernetes cluster and re-established N3 interface. Applied network policy fix for pod-to-pod routing. Session continuity restored via re-anchor procedure.",
        ),
        (
            "5G NR {vendor} gNodeB license capacity breach at {site}. Maximum licensed active UEs reached causing new connection rejection for {count} subscribers.",
            "Requested emergency license extension from vendor portal. Applied license update file and restarted license manager service. Initiated procurement process for permanent capacity upgrade.",
        ),
    ],

    "4G-LTE": [
        (
            "{vendor} eNodeB at {site} reported S1 interface failure to MME. All attached UEs detached; voice calls and data sessions dropped for {count} subscribers.",
            "Identified misconfigured SCTP multihoming parameter after recent software upgrade. Corrected SCTP association configuration and restored S1-MME and S1-U interfaces.",
        ),
        (
            "LTE eNodeB {vendor} at {site} experienced X2 handover failure. Inter-eNodeB mobility success rate dropped to 28%, causing call drops at cell edge.",
            "Reset X2 interface and re-synchronized neighbor cell list. Adjusted A3 event time-to-trigger from 320 ms to 160 ms. Handover success rate recovered to 96%.",
        ),
        (
            "LTE cell at {site} showing PDCP layer RoHC decompression failures on {vendor} eNodeB. Packet loss rate 8% impacting VoLTE call quality (MOS < 2.5).",
            "Disabled RoHC compression as temporary workaround. Opened vendor TAC case. Applied firmware patch addressing RoHC context synchronization defect. Re-enabled RoHC after validation.",
        ),
        (
            "{vendor} eNodeB GPS disciplined oscillator (GPSDO) at {site} reported holdover event. LTE timing accuracy degraded, causing increased inter-cell interference.",
            "Reconnected loose GPS antenna cable. Forced GPS receiver re-acquisition. Verified 1PPS signal integrity within ±100 ns. Oscillator re-locked to GPS after 8 minutes.",
        ),
        (
            "LTE eNodeB {vendor} at {site} reported Uu interface CQI collapse. Average DL CQI dropped from 12 to 3, causing MCS fallback and 70% throughput reduction.",
            "Identified antenna port connector corrosion. Cleaned and re-terminated N-type connectors. Applied torque to spec. DL CQI recovered to average 11. Scheduled preventive maintenance.",
        ),
        (
            "Mass call drop event on {vendor} LTE site {site}. CSFB (Circuit Switched Fallback) failure rate reached 45% due to SGs interface timer misconfiguration.",
            "Corrected SGsAP connection keep-alive timer on MME side. Restarted SGs interface and verified IMSI detach/attach cycle. CSFB success rate restored to 99.2%.",
        ),
        (
            "{vendor} eNodeB at {site} showed persistent RRC setup failure rate of 18%. Signaling congestion due to attach storm from IoT device firmware update.",
            "Applied RRC connection establishment access class barring (ACB) for Class 0-9. Coordinated IoT platform team to stagger firmware push. Congestion cleared within 25 minutes.",
        ),
        (
            "LTE Carrier Aggregation (CA) deactivated on {vendor} eNodeB at {site}. SCell configuration failure preventing CA activation for {count} capable UEs.",
            "Identified incorrect CA combination band list in SCell configuration. Corrected CA_42C configuration. Re-activated CA on SCell. Average UE throughput improved by 40%.",
        ),
        (
            "LTE eNodeB {vendor} at {site} experienced uplink PUSCH interference from adjacent TDD network operating on overlapping frequency band.",
            "Coordinated frequency plan adjustment with interfering operator. Applied UL interference rejection combining (IRC) algorithm. Deployed UL interference detection and reporting trigger.",
        ),
        (
            "{vendor} eNodeB software process (OAM agent) crashed at {site}. Remote management and configuration interface became unavailable. Alarms not forwarded to EMS for 35 minutes.",
            "Restarted OAM agent process via local CLI. Verified alarm queue synchronization with EMS. Applied vendor software patch to address OAM memory corruption issue.",
        ),
        (
            "LTE eNodeB {vendor} at {site} reported high RACH congestion. PRACH preamble collision rate >30% during morning peak causing 15% call setup failures.",
            "Reduced PRACH configuration index to increase preamble opportunity slots. Enabled power ramping step optimization. RACH success rate improved to 98.5% during peak hour.",
        ),
        (
            "{vendor} eNodeB at {site} lost backhaul connectivity due to IP routing loop introduced by misconfigured static route. Cell site isolated for {outage} minutes.",
            "Identified duplicate static route entry causing routing loop. Removed conflicting route and restored correct default gateway. Verified BGP session re-establishment with core router.",
        ),
        (
            "LTE SON (Self-Organizing Network) MLB function on {vendor} eNodeB caused unexpected load redistribution at {site}. High-priority users migrated to congested cells.",
            "Disabled MLB function pending parameter review. Recalibrated MLB threshold values and UE throughput weighting. Re-enabled MLB in monitoring mode with conservative parameters.",
        ),
        (
            "{vendor} eNodeB at {site} experienced antenna tilt misconfiguration after remote electrical tilt (RET) actuator failure. Coverage hole created affecting {count} users.",
            "Replaced faulty AISG RET actuator. Reset antenna mechanical and electrical tilt to planned configuration. Verified coverage and interference using drive test results.",
        ),
        (
            "LTE VoLTE bearer establishment failure on {vendor} eNodeB at {site}. GBR bearer allocation rejected due to QoS policy conflict in PCRF.",
            "Corrected QCI-1 GBR bandwidth allocation profile in PCRF policy rules. Restarted Gx interface session. VoLTE call setup success rate restored to 99.8%.",
        ),
        (
            "{vendor} eNodeB at {site} reported DL HARQ retransmission rate exceeding 25% on TDD UL-DL configuration 2. Subframe assignment mismatch causing co-channel interference.",
            "Synchronized TDD UL-DL configuration across all cells in cluster. Applied GPS-based frame boundary alignment. DL HARQ retransmission reduced to 3.2%.",
        ),
        (
            "LTE eNodeB {vendor} power supply unit failed at {site} causing partial cell shutdown. Battery backup activated; {count} active sessions maintained on reduced capacity.",
            "Replaced failed AC/DC power supply module. Transferred load to main power feed. Verified rectifier output voltage and float charge parameters. Full capacity restored.",
        ),
    ],

    "3G-UMTS": [
        (
            "{vendor} NodeB at {site} reported Iub interface Abis link failure. ATM AAL2 path connectivity lost causing all active voice calls on WCDMA R99 to drop.",
            "Identified ATM cross-connect misconfiguration on transmission equipment. Re-provisioned AAL2 paths and restored Iub interface. Verified NBAP common procedures and AAL2 establishment.",
        ),
        (
            "WCDMA NodeB {vendor} at {site} experienced pilot pollution from 6 strong pilot signals. Ec/No degraded to -18 dB causing persistent active set update failures.",
            "Conducted pilot pollution audit using TEMS drive test. Reduced pilot power on 3 dominant interferers. Adjusted handover soft/softer margins. Active set management normalized.",
        ),
        (
            "{vendor} RNC at {site} reported HSDPA scheduler process exception. HS-DSCH throughput dropped to zero for {count} users during scheduler restart cycle.",
            "Restarted HSDPA scheduler process on RNC blade. Applied vendor patch to address HS-DSCH MAC-hs reordering buffer overflow. CQI feedback loop re-established.",
        ),
        (
            "3G UMTS NodeB {vendor} at {site} showed excessive downlink scrambling code collision. Adjacent NodeB same PSC assignment causing UE handover confusion.",
            "Re-planned Primary Scrambling Code (PSC) allocation using neighbor audit tool. Assigned unique PSC to conflicting NodeBs. Verified handover performance post-change.",
        ),
        (
            "{vendor} NodeB power amplifier at {site} overheated and entered protection mode. CPICH Ec/Io degraded causing coverage loss over 2.5 km radius.",
            "Emergency replacement of PA module. Re-calibrated CPICH transmit power to -10 dBm. Verified coverage with before/after RSCP measurements from nearby test UEs.",
        ),
        (
            "WCDMA {vendor} NodeB at {site} reported clock reference failure. SFN (System Frame Number) desynchronization caused radio link failure for all active connections.",
            "Replaced GPS timing module on NodeB. Re-synchronized SFN boundary to network reference. Verified timing accuracy within ±500 ns specification.",
        ),
        (
            "{vendor} RNC IU-PS interface to SGSN became unstable at {site}. GTP-C path failure caused PDP context deactivations for {count} data users.",
            "Restarted IU-PS SCCP signaling stack. Re-established IU-PS RAB assignments. Verified GTP path management echo response and PDP context re-activation.",
        ),
        (
            "WCDMA uplink noise rise alarm on {vendor} NodeB at {site}. Cell breathing reduced coverage by 40% due to high interference floor from co-channel interference.",
            "Identified faulty low-noise amplifier in receive path. Replaced LNA module. Noise figure improved from 12 dB to 2.1 dB. Cell coverage restored to planned range.",
        ),
        (
            "{vendor} NodeB at {site} experienced Abis microwave backhaul degradation. High BER on E1 circuits caused Iub signaling failures and sporadic call drops.",
            "Adjusted microwave link polarization and alignment. Replaced degraded ODU with higher-gain antenna. E1 BER improved to <1E-9. No further Iub signaling anomalies observed.",
        ),
        (
            "3G UMTS {vendor} NodeB at {site} reported high number of radio link failures (RLF). UE-side measurement gap misconfiguration causing blind handover execution.",
            "Corrected measurement gap pattern configuration in RNC. Reduced compressed mode activation threshold. RLF rate decreased from 3.2% to 0.4%.",
        ),
        (
            "{vendor} RNC software upgrade failed at {site} resulting in partial NodeB disconnection. 12 NodeBs lost Iub connectivity during rollback procedure.",
            "Executed emergency rollback to previous RNC software version. Re-established Iub connections for all affected NodeBs. Post-rollback stability confirmed over 2-hour monitoring period.",
        ),
        (
            "WCDMA CS domain AMR voice quality degraded on {vendor} NodeB at {site}. SHO (Soft Handover) overhead exceeded 45% causing uplink capacity constraint.",
            "Optimized soft handover window parameters (W1/W2). Reduced add/drop thresholds to decrease SHO zone overlap. SHO overhead reduced to 28%. AMR voice MOS improved.",
        ),
        (
            "{vendor} NodeB at {site} reported VSWR alarm on antenna port 2. Return loss degraded to 8 dB indicating antenna feeder water ingress.",
            "Replaced weatherproofed jumper cable showing water ingress. Applied self-amalgamating tape to all connectors. VSWR improved to 1.15:1. Antenna port alarm cleared.",
        ),
        (
            "3G UMTS NodeB {vendor} at {site} showed DCH (Dedicated Channel) setup failure rate of 22%. Cell congestion due to insufficient channelization code tree capacity.",
            "Reduced maximum DL SF-32 code allocation per UE. Enabled HSPA code sharing optimization. DCH setup failure reduced to 1.1%. Scheduled capacity dimensioning review.",
        ),
        (
            "{vendor} NodeB at {site} lost primary E1 backhaul due to fiber cut. Secondary E1 activated but Iub capacity reduced to 2 Mbps causing severe congestion.",
            "Coordinated emergency fiber repair with transmission team. Primary E1 restored within {outage} minutes. Traffic load re-balanced across primary and secondary Iub circuits.",
        ),
        (
            "WCDMA inter-frequency handover failure on {vendor} NodeB at {site}. Missing neighbor in compressed mode measurement event 2D triggering blank spot at cell boundary.",
            "Added missing inter-frequency neighbor relation in RNC. Re-calibrated compressed mode triggering thresholds. Inter-frequency IRAT HO success rate improved from 61% to 94%.",
        ),
    ],

    "Fiber-Optic": [
        (
            "Fiber cut detected on {vendor} DWDM span between {site} and adjacent hub. 48-fiber cable severed during road construction, causing total loss of {count} active wavelengths.",
            "Emergency crew dispatched. Fusion spliced 48 fiber strands. OTDR verified splice loss < 0.1 dB. Restored DWDM channels sequentially after splice completion.",
        ),
        (
            "{vendor} optical amplifier EDFA at {site} reported gain tilt alarm. Uneven channel power distribution caused BER degradation on 12 of 80 DWDM channels.",
            "Rebalanced EDFA gain profile using VOA per-channel attenuation adjustment. Optimized tilt compensation. Verified OSNR > 20 dB on all channels after rebalancing.",
        ),
        (
            "Fiber-Optic cable at {site} showing high attenuation (>0.35 dB/km) on 6 fiber pairs. Degraded splices from lightning strike causing intermittent DWDM channel impairments.",
            "Identified degraded splice points using OTDR. Performed re-splicing at 3 locations. Attenuation reduced to 0.19 dB/km. Monitored channel BER for 4 hours post-repair.",
        ),
        (
            "{vendor} ROADMs at {site} reported optical power out-of-range alarm. WSS (Wavelength Selective Switch) port failure causing 20 channels to drop on express path.",
            "Replaced faulty WSS module in ROADM degree 3. Re-provisioned optical power levels. Verified channel through-traffic and add/drop port functionality.",
        ),
        (
            "Fiber-Optic link between {site} and core PoP showing chromatic dispersion exceeding 1700 ps/nm. DCF module failure causing 100G coherent transponder Q-factor degradation.",
            "Replaced defective DCF module. Re-optimized dispersion compensation using tunable dispersion compensator. Pre-FEC BER improved to <1E-4 on affected 100G channels.",
        ),
        (
            "{vendor} submarine cable landing station at {site} reported sea cable fault. Branching unit failure at 85 km depth causing complete loss of trans-oceanic capacity.",
            "Deployed cable ship for deep-sea repair. Isolated fault section using OTDR. Replaced branching unit. Full capacity restored after 72-hour marine repair operation.",
        ),
        (
            "Fiber duct flooding at {site} caused by burst water main. {count} fibers showing >3 dB attenuation increase due to water in splice enclosures.",
            "Dewatered duct and inspected all splice enclosures. Replaced water-damaged closure seals. Re-spliced degraded fiber pairs. Installed hydrophobic gel in at-risk duct sections.",
        ),
        (
            "{vendor} OTN switch at {site} reported ODU2 path AIS-P (Alarm Indication Signal - Path). Cross-connect programming error caused mis-routing of 10G service circuit.",
            "Identified incorrect ODU2 cross-connect in OTN switch database. Corrected switching matrix configuration. Verified end-to-end ODU2 path continuity using in-band OAM.",
        ),
        (
            "Fiber-Optic patch cord failure on {vendor} transponder shelf at {site}. Contaminated LC connector causing -6 dB insertion loss on 400G ZR channel.",
            "Cleaned LC connector with fiber optic cleaning kit. Inspected end-face with inspection probe (IEC 61300-3-35). Replaced patch cord. Optical power restored to nominal.",
        ),
        (
            "{vendor} DWDM system at {site} showing polarization mode dispersion (PMD) alarm on 32 km span. Old fiber plant with PMD > 40 ps causing 100G signal impairment.",
            "Re-routed affected wavelengths over alternate lower-PMD fiber path. Initiated fiber characterization project. Scheduled fiber plant upgrade to G.654.E specification.",
        ),
        (
            "Optical fiber cable at {site} suffered micro-bending damage due to improper installation of cable tray clamps. BER on 3 channels degraded to 1E-5.",
            "Removed over-tight cable clamps causing micro-bending. Re-routed fiber with proper bend radius (> 30 mm). Channel BER restored to <1E-12 after tension relief.",
        ),
        (
            "{vendor} EDFA pump laser at {site} degraded, reducing output power by 8 dB. OSNR margin exhausted causing 4 channels to fall below FEC threshold.",
            "Replaced EDFA pump laser module. Restored output power to +17 dBm. Recalibrated per-channel gain and noise figure. All channels returned within OSNR specification.",
        ),
        (
            "Fiber splice enclosure at {site} damaged by rodent gnawing. 8 fiber pairs severed, causing service disruption on multiple enterprise leased line circuits.",
            "Installed stainless steel armored splice enclosure replacement. Re-spliced all 8 fiber pairs. Applied rodent deterrent compound in duct. All leased line circuits restored.",
        ),
        (
            "{vendor} coherent DSP transponder at {site} failed in-service. Carrier phase recovery loop unlocked causing 400G ZR+ link to drop after 6 dB OSNR margin reduction.",
            "Hot-swapped faulty coherent DSP line card. Re-provisioned carrier phase tracking parameters. Verified constellation diagram and pre-FEC BER. Link restored at full 400G capacity.",
        ),
        (
            "Fiber-Optic ring at {site} experienced dual-node failure due to simultaneous power outage and cable cut. APS (Automatic Protection Switching) failed to recover.",
            "Restored generator power to both nodes. Repaired fiber cut on protection segment. Re-initialized APS state machine. Ring topology restored and re-locked to primary path.",
        ),
        (
            "{vendor} ROADMs at {site} showed launch power instability due to software bug in automatic power control (APC) loop. Power oscillations caused 3 channel outages.",
            "Disabled automatic power control and set manual launch power targets. Applied vendor firmware fix for APC feedback loop. Re-enabled APC after firmware validation.",
        ),
    ],

    "MPLS-Core": [
        (
            "{vendor} core router at {site} experienced BGP session flap with peer. 15,000 prefixes withdrawn causing traffic black-holing for {count} enterprise customers.",
            "Identified TCP session reset due to BGP hold-timer expiry. Increased BGP keepalive from 10s to 30s. Applied BFD for rapid failure detection. BGP session stabilized.",
        ),
        (
            "MPLS LDP label distribution failure on {vendor} router at {site}. LSP path broke after FIB inconsistency caused by in-service software upgrade.",
            "Cleared LDP session and forced full label re-exchange. Verified FIB/LFIB consistency using 'show mpls forwarding'. Applied ISSU patch to address FIB update race condition.",
        ),
        (
            "{vendor} PE router at {site} reported MPLS-TP OAM CC (Continuity Check) failure on 15 pseudowires. BFD session timeout caused false protection switchover.",
            "Adjusted BFD timer values to prevent false positives during high CPU events. Cleared pseudowire state and re-established BFD sessions. Revert standby PE to backup state.",
        ),
        (
            "MPLS-Core {vendor} router at {site} showed CPU utilization at 98% due to BGP scanner process. Route dampening misconfiguration caused prefix instability storm.",
            "Applied route dampening suppression threshold adjustment. Used 'clear ip bgp soft' to reset policy. CPU returned to 15% within 5 minutes. Implemented rate limiting on BGP updates.",
        ),
        (
            "OSPF adjacency loss between {vendor} core routers at {site}. Dead interval mismatch after manual configuration change caused IS-IS/OSPF split-brain condition.",
            "Corrected OSPF hello/dead interval to match across all interfaces. Re-established neighbor adjacency. Verified full SPF convergence. Restored MPLS traffic engineering tunnels.",
        ),
        (
            "{vendor} MPLS backbone router at {site} experienced line card failure. 4 x 100G interfaces went down, causing traffic re-routing over congested backup paths.",
            "Replaced failed line card (FPC slot 3). Re-established all 100G interface adjacencies. Rebalanced ECMP traffic. Verified MPLS TE tunnel re-optimization completed.",
        ),
        (
            "MPLS QoS DSCP marking misconfiguration on {vendor} PE router at {site}. Enterprise voice traffic (EF DSCP46) downgraded to best-effort, causing VoIP quality degradation.",
            "Corrected ingress QoS policy map DSCP classification. Applied updated service policy to customer-facing interfaces. Verified EF queue scheduling and policing parameters.",
        ),
        (
            "{vendor} MPLS core router at {site} showed memory exhaustion on route processor. BGP RIB exceeded 1.2M prefixes triggering memory protection killing processes.",
            "Applied prefix-list to limit full BGP table absorption. Increased RP memory from 32 GB to 64 GB. Restarted BGP process and verified RIB re-population.",
        ),
        (
            "MPLS-TP protection switching failure on {vendor} router ring at {site}. Working LSP failure did not trigger protection switch within 50 ms SLA.",
            "Identified protection switching state machine stuck in 'Wait to Restore' mode. Reset PSC (Protection State Coordination) protocol. Verified <50 ms protection switching with test failover.",
        ),
        (
            "{vendor} BGP route reflector at {site} crashed due to malformed UPDATE message from external peer. All iBGP clients lost routes for 8 minutes during RR restart.",
            "Implemented BGP error handling with 'bgp soft-reconfig' and neighbor error-tolerance. Applied vendor patch for malformed attribute parsing. RR restarted with graceful restart enabled.",
        ),
        (
            "MPLS traffic engineering RSVP-TE tunnel establishment failure on {vendor} router at {site}. Bandwidth constraint violation prevented LSP setup over primary path.",
            "Re-ran offline TE path computation with updated bandwidth topology. Applied 'mpls traffic-eng reoptimize' command. Tunnels established over alternate path with sufficient bandwidth.",
        ),
        (
            "{vendor} MPLS core suffered IS-IS database overflow at {site}. LSP fragmentation and ATT bit propagation caused sub-optimal routing for 20 minutes.",
            "Increased IS-IS LSP MTU to 1492 bytes. Implemented IS-IS mesh groups to reduce LSP flooding. Database overflow alarm cleared. Routing table consistency verified.",
        ),
        (
            "MPLS VPN L3VPN route leakage detected on {vendor} PE router at {site}. Import RT misconfiguration caused {count} enterprise customer routes to appear in wrong VRF.",
            "Identified incorrect import route-target on affected VRF. Corrected RT import policy and cleared VRF routing table. Verified route isolation between all customer VRFs.",
        ),
        (
            "{vendor} core router ECMP load balancing failure at {site}. Hash polarization caused 95% of traffic to concentrate on single link, causing link congestion.",
            "Modified ECMP hash seed value to resolve polarization. Verified balanced traffic distribution across all 4 ECMP links. Implemented entropy label for better randomization.",
        ),
        (
            "MPLS-Core {vendor} router at {site} experienced packet reordering on L2VPN pseudowire due to ECMP. TCP throughput impacted for {count} financial services customers.",
            "Applied control-word encapsulation to L2VPN pseudowires to prevent ECMP-induced reordering. Verified TCP performance improvement using iperf testing. Jitter reduced to <1 ms.",
        ),
    ],

    "RAN": [
        (
            "{vendor} RAN controller experienced high CPU utilization at {site}. Scheduler overload caused radio resource management delays, resulting in 18% call setup failure rate.",
            "Identified rogue UE causing excessive scheduling requests. Implemented UE barring rule. Restarted RAN scheduler process. CPU normalized to 35%. Call setup success rate restored.",
        ),
        (
            "RAN site {site} reporting antenna VSWR alarm on sector 2. Water ingress in feeder cable causing 3 dB insertion loss and 40% coverage reduction.",
            "Replaced weatherproofed feeder cable assembly. Applied cold shrink tubing on all RF connectors. VSWR improved to 1.12:1. Sector 2 coverage restored to design contour.",
        ),
        (
            "{vendor} BBU (Baseband Unit) hardware fault at {site}. CPRI link to 3 RRUs failed causing complete site blackout affecting {count} active subscribers.",
            "Replaced faulty BBU processing board. Re-established all CPRI links. Verified radio frame synchronization. All sectors returned to service after 45-minute replacement procedure.",
        ),
        (
            "RAN inter-frequency measurement configuration error on {vendor} equipment at {site}. UEs failing to perform IRAT handover from LTE to UMTS in poor coverage areas.",
            "Corrected measurement object frequency list in RRM policy. Added missing UMTS ARFCN to inter-frequency neighbor list. IRAT HO success rate improved from 34% to 91%.",
        ),
        (
            "{vendor} Remote Radio Unit (RRU) temperature alarm at {site}. Cooling failure caused power reduction to 50%, decreasing coverage and capacity significantly.",
            "Replaced blocked heat sink and faulty fan module in RRU. Temperature decreased from 78°C to 42°C. Full transmit power restored after 30-minute thermal stabilization.",
        ),
        (
            "RAN {vendor} SON Mobility Robustness Optimization (MRO) triggered excessive HO parameter changes at {site}. Ping-pong handover rate increased to 12%.",
            "Disabled MRO auto-optimization pending review. Manually reset HO parameters to baseline values. Ping-pong rate reduced to 0.8%. MRO re-enabled with conservative change limits.",
        ),
        (
            "{vendor} RAN software upgrade failed at {site}. Rollback activated but 5 NodeBs stuck in software download state, causing service outage.",
            "Performed manual software reset on affected NodeBs via local CLI. Cleared corrupted software package. Executed rollback installation. All NodeBs returned to previous stable software.",
        ),
        (
            "RAN site {site} experiencing uplink interference from co-channel industrial WiFi deployment in adjacent building. PUSCH SINR degraded to -5 dB on band 3.",
            "Reported co-channel interference to site planning team. Implemented UL interference rejection combining. Coordinated with building management to relocate WiFi access points.",
        ),
        (
            "{vendor} RAN capacity planning threshold breach at {site}. PRB utilization sustained above 90% for 3 consecutive hours causing new user admission rejections.",
            "Deployed temporary additional carriers via spectrum sharing. Submitted capacity upgrade order for new BBU and additional spectrum allocation. Short-term congestion resolved.",
        ),
        (
            "RAN timing synchronization failure at {site}. {vendor} BBU lost IEEE 1588v2 PTP synchronization from aggregation node, triggering LTE cell downgrade.",
            "Identified PTP boundary clock misconfiguration on aggregation switch. Corrected PTP domain number and clock class settings. BBU re-acquired PTP lock within 3 minutes.",
        ),
        (
            "{vendor} RAN site at {site} reported high paging failure rate (28%). Paging area mismatch due to TA (Tracking Area) boundary inconsistency between neighboring cells.",
            "Corrected Tracking Area Code (TAC) assignment for border cells. Synchronized TA boundary between adjacent RAN controllers. Paging failure rate reduced to 0.5%.",
        ),
        (
            "RAN {vendor} equipment at {site} suffered lightning strike on tower. Surge protectors failed, damaging 2 RRUs and BBU RF interface boards.",
            "Replaced damaged RRUs and BBU RF boards. Installed enhanced surge protection devices with 20 kA rating. Performed antenna system VSWR validation. Site fully restored.",
        ),
        (
            "{vendor} RAN load balancing failure at {site}. MLB algorithm migrated {count} users to already-congested neighbor cells, worsening network performance.",
            "Disabled automatic MLB and performed manual load rebalancing. Updated neighbor cell capacity weights in MLB configuration. Deployed additional capacity to bottleneck cells.",
        ),
        (
            "RAN site {site} showing high call drop rate (8.5%) due to {vendor} coverage gap created by incorrect antenna azimuth after maintenance work.",
            "Corrected antenna azimuth from 270° back to planned 320°. Verified coverage using scanner measurements. Call drop rate normalized to 0.3% post-correction.",
        ),
        (
            "{vendor} RAN management system lost connectivity to {count} radio sites at {site} region. OAM IP network reachability failure caused mass alarm suppression.",
            "Identified routing table corruption on OAM aggregation router. Restored correct static routes. Re-established SNMP/NETCONF sessions to all affected radio sites.",
        ),
    ],

    "IP-Core": [
        (
            "{vendor} core IP router at {site} experienced control plane CPU spike to 100%. Route processor lockup caused BGP session drops to 45 peers, triggering network-wide reconvergence.",
            "Identified runaway OSPF SPF calculation triggered by link flap. Applied SPF throttle timers. Restarted control plane processes. BGP sessions re-established within 4 minutes.",
        ),
        (
            "IP-Core {vendor} router at {site} reported OSPF neighbor adjacency failure. MTU mismatch on core link after router replacement caused Database Description packet rejection.",
            "Set interface MTU to 9000 bytes on both ends of core link. Cleared OSPF process and forced neighbor re-establishment. Full LSA database synchronization completed.",
        ),
        (
            "{vendor} PE router at {site} experienced hardware forwarding engine failure. Packets punted to software forwarding, causing 10x latency increase for transit traffic.",
            "Identified failed TCAM (Ternary Content Addressable Memory) bank on forwarding ASIC. Reloaded line card to perform TCAM self-test. Forwarding engine resumed hardware operation.",
        ),
        (
            "IP-Core traffic surge at {site} caused {vendor} router interface utilization to reach 98%. Buffer bloat increased round-trip latency from 5 ms to 180 ms.",
            "Implemented WRED (Weighted Random Early Detection) on congested interfaces. Activated traffic engineering to redistribute load. Emergency bandwidth upgrade order placed.",
        ),
        (
            "{vendor} network at {site} experienced BGP route dampening incorrectly suppressing stable prefixes. {count} enterprise prefixes unreachable for 40 minutes.",
            "Cleared all damped routes with 'clear ip bgp dampening'. Revised dampening parameters to increase half-life from 15 to 45 minutes. Stable prefixes restored immediately.",
        ),
        (
            "IP-Core {vendor} router at {site} lost NTP synchronization. Clock drift of 8 seconds causing RADIUS authentication timestamp rejection, blocking {count} user logins.",
            "Configured additional NTP servers with authentication. Forced manual clock synchronization using 'ntp update-calendar'. RADIUS authentication restored immediately.",
        ),
        (
            "{vendor} internet peering router at {site} received BGP UPDATE with AS_PATH loop. Malformed route caused recursive routing lookup failure, dropping 30% of customer traffic.",
            "Implemented AS_PATH filter to reject routes with our own ASN. Applied BGP prefix validation using RPKI. Malformed routes filtered. Traffic routing normalized.",
        ),
        (
            "IP-Core {vendor} router at {site} showed packet fragmentation issue on GRE tunnel. MTU black hole caused TCP sessions to stall for applications using path MTU discovery.",
            "Enabled 'ip tcp adjust-mss 1452' on tunnel interfaces. Configured PMTUD responder. Added ICMP type 3 code 4 passthrough rules. TCP session stalls eliminated.",
        ),
        (
            "{vendor} router at {site} experienced SNMP MIB polling overload. Excessive NMS polling frequency caused management plane CPU saturation, delaying routing protocol timers.",
            "Reduced SNMP polling frequency from 30s to 300s for non-critical OIDs. Implemented SNMP view to limit accessible MIB objects. Management CPU load reduced to 12%.",
        ),
        (
            "IP-Core {vendor} router at {site} experienced STP (Spanning Tree Protocol) loop in management network VLAN. Broadcast storm caused management plane disruption for 12 minutes.",
            "Enabled BPDU Guard on all edge ports. Removed redundant management network cable causing loop. Implemented Rapid PVST+ for faster convergence. Storm control enabled on edge interfaces.",
        ),
        (
            "{vendor} core router at {site} reported ECMP hash algorithm producing uneven traffic distribution. 1 of 8 links carrying 40% of all traffic.",
            "Modified ECMP hash polynomial to include L4 source/destination ports. Verified equal distribution across all 8 links with <5% variance. Traffic engineering reoptimized.",
        ),
        (
            "IP-Core {vendor} router at {site} experienced ACL compilation failure after policy update. 500 ms ACL recalculation delay caused packet drops during security policy push.",
            "Implemented incremental ACL update mechanism. Staged ACL changes during maintenance window. Optimized ACL sequence to reduce TCAM space consumption.",
        ),
        (
            "{vendor} router at {site} lost BGP session to upstream provider due to GTSM (Generalized TTL Security Mechanism) misconfiguration. External connectivity dropped for {count} customers.",
            "Corrected GTSM TTL value to 254 for eBGP multihop session. Re-established BGP session to upstream provider. Default route restored. Customer traffic normalized.",
        ),
        (
            "IP-Core {vendor} router at {site} experienced QoS policy inconsistency after IOS upgrade. DSCP remarking incorrect, causing VoIP traffic to be treated as best-effort.",
            "Re-applied QoS policy map after upgrade. Corrected DSCP-to-queue mapping table. Verified EF queue scheduling (PQ) operational. VoIP MOS scores improved to 4.2.",
        ),
        (
            "{vendor} internet exchange router at {site} received BGP session reset from 12 route server peers. MD5 authentication key mismatch after planned maintenance caused peer drops.",
            "Re-synchronized BGP MD5 keys with route server operator. Re-established all 12 BGP sessions. Verified prefix acceptance from all IXP peers. Added key rotation procedure to maintenance checklist.",
        ),
    ],

    "Microwave-Backhaul": [
        (
            "{vendor} microwave link at {site} showed severe rain fade attenuation. Link availability dropped to 88% in heavy monsoon. ACM adapted from 256QAM to QPSK causing 75% throughput reduction.",
            "Implemented XPIC (Cross-Polarization Interference Cancellation) to improve link budget. Added 6 dB fade margin by upgrading to higher-gain antenna. ACM minimum modulation raised to 16QAM.",
        ),
        (
            "Microwave hop {vendor} between {site} and adjacent site experiencing co-channel interference. Frequency reuse plan violation causing sustained C/I ratio below 15 dB threshold.",
            "Performed frequency coordination audit. Re-assigned channel plan to avoid co-channel conflict. Applied adaptive beam steering. C/I ratio improved to 28 dB. Link stability restored.",
        ),
        (
            "{vendor} microwave ODU (Outdoor Unit) at {site} reported hardware fault. Local oscillator phase lock failure causing complete link loss. Backhaul traffic rerouted to fiber backup.",
            "Replaced faulty ODU unit. Re-aligned antenna bearing (azimuth 247°, elevation 1.2°). Verified RSL within -1 dB of nominal. Reverted traffic from fiber backup after link restoration.",
        ),
        (
            "Microwave backhaul {vendor} at {site} lost alignment due to tower sway in high wind (>90 km/h). RSL dropped 14 dB below threshold causing link outage.",
            "Dispatched tower rigger crew post-storm. Re-aligned both ends to boresight. Applied fine-tuning using RSL maximization procedure. Link re-established at nominal RSL.",
        ),
        (
            "{vendor} microwave backhaul capacity exhaustion at {site}. Adaptive modulation locked at QPSK due to insufficient link budget, limiting throughput to 150 Mbps.",
            "Upgraded antenna from 0.3m to 0.6m dish, gaining 6 dBi. Link budget improved enabling 256QAM operation. Throughput increased to 800 Mbps. Capacity upgrade completed.",
        ),
        (
            "Microwave link {vendor} at {site} showed increased BER after nearby construction modified Fresnel zone clearance. Ground reflection multipath causing signal cancellation.",
            "Raised antenna mast height by 3 meters to restore Fresnel zone clearance. Performed space diversity analysis. Space diversity upgrade implemented. BER reduced to <1E-9.",
        ),
        (
            "{vendor} microwave backhaul site {site} lost power. Battery backup depleted after 4-hour mains failure. Link down causing backhaul outage for 3 dependent radio sites.",
            "Restored mains power and recharged battery bank. Extended battery autonomy from 4 to 8 hours. Generator auto-start system tested. Added power monitoring alerting.",
        ),
        (
            "Microwave {vendor} IDU (Indoor Unit) at {site} experienced Ethernet port MAC address table overflow. Traffic flooding caused bandwidth saturation on backhaul link.",
            "Cleared MAC address table and applied MAC address limit per port. Implemented port security with sticky MAC learning. Traffic flooding eliminated. Backhaul utilization normalized.",
        ),
        (
            "{vendor} microwave Ethernet backhaul at {site} showing excessive packet delay variation (PDV > 2 µs). IEEE 1588 PTP synchronization degraded, affecting LTE timing.",
            "Enabled PTP-aware packet processing on all microwave hops. Applied asymmetry compensation. PDV reduced to <200 ns. LTE synchronization accuracy restored to ±100 ns.",
        ),
        (
            "Microwave link {vendor} at {site} experienced atmospheric ducting event. Abnormal tropospheric refraction caused RSL increase by 20 dB, triggering overload and BER increase.",
            "Applied adaptive threshold adjustment during ducting event. Enabled automatic level control to handle RSL excursions. Implemented ducting event monitoring and alerting.",
        ),
        (
            "{vendor} microwave backhaul at {site} lost redundancy after protection link failure. Single point of failure created for {count} radio sites.",
            "Replaced failed protection link ODU. Re-established 1+1 HSB (Hot Standby) protection. Performed protection switching test confirming <50 ms switchover time.",
        ),
        (
            "Microwave {vendor} backhaul at {site} showed STM-1 framing errors. E1 circuit synchronization failure causing PCM voice quality degradation.",
            "Replaced STM-1 tributary card showing framing anomalies. Re-synchronized E1 frame alignment. Verified PCM voice quality using BER test equipment. No further framing errors.",
        ),
        (
            "{vendor} microwave link at {site} reported antenna feeder pressurization loss. Moisture ingress in unpressurized waveguide causing increased insertion loss.",
            "Replaced pressurization unit and repaired waveguide flange seal. Re-pressurized feeder system to 0.5 bar. Insertion loss reduced from 2.8 dB to 0.9 dB. Feeder integrity alarm cleared.",
        ),
        (
            "Microwave backhaul {vendor} at {site} experienced software-defined radio (SDR) licensing failure. ACM locked to minimum modulation (QPSK) until license renewed.",
            "Applied emergency 30-day software license extension. Submitted permanent license purchase order. ACM functionality restored. Link capacity returned to 1 Gbps nominal.",
        ),
        (
            "{vendor} microwave backhaul at {site} showing packet loss of 0.3% due to Ethernet frame size mismatch. Jumbo frame (9000 byte) not supported on intermediate hop.",
            "Corrected MTU configuration to 1500 bytes on all microwave Ethernet interfaces. End-to-end MTU alignment verified. Packet loss eliminated. Backhaul throughput normalized.",
        ),
    ],

    "Cloud-RAN": [
        (
            "{vendor} Cloud-RAN vCU (Virtual Central Unit) pod at {site} evicted due to Kubernetes node memory pressure. Active sessions dropped for {count} UEs during pod rescheduling.",
            "Increased memory request/limit for vCU pod to 16 GB. Added node affinity rules to prevent co-location with memory-intensive workloads. PodDisruptionBudget applied for high availability.",
        ),
        (
            "Cloud-RAN {vendor} fronthaul network latency spike detected at {site}. eCPRI frame delay exceeded 100 µs threshold causing L1 timing violations and cell downgrade.",
            "Identified network policy misconfiguration causing fronthaul traffic to traverse extra hop. Applied dedicated VLAN with strict priority queueing. Fronthaul latency reduced to 28 µs.",
        ),
        (
            "{vendor} Cloud-RAN vDU (Virtual DU) scaling failure at {site}. Auto-scaling policy did not trigger during traffic surge, causing cell congestion for {count} subscribers.",
            "Manually scaled vDU replicas from 2 to 6. Updated HPA (Horizontal Pod Autoscaler) CPU threshold from 80% to 60%. Configured min/max replica bounds. Congestion resolved.",
        ),
        (
            "Cloud-RAN container image pull failure at {site}. {vendor} vCU/vDU pods stuck in ImagePullBackOff state after container registry authentication token expired.",
            "Refreshed registry authentication secret in Kubernetes namespace. Restarted pod deployment. Implemented automatic secret rotation with 24-hour token refresh cycle.",
        ),
        (
            "{vendor} Cloud-RAN NFV infrastructure at {site} experienced NUMA (Non-Uniform Memory Access) misconfiguration. vDU experiencing high memory latency reducing L1 real-time performance.",
            "Applied NUMA topology-aware scheduling for vDU pods. Pinned CPU cores and memory to same NUMA node. L1 processing latency reduced from 1.8 ms to 0.3 ms.",
        ),
        (
            "Cloud-RAN {vendor} O-DU software exception at {site}. FAPI (Functional API) message queue overflow caused L2 scheduler crash affecting {count} active users.",
            "Restarted O-DU L2 scheduler container. Increased FAPI message queue depth from 1024 to 4096. Applied vendor patch for scheduler queue overflow handling.",
        ),
        (
            "{vendor} Cloud-RAN OpenFronthaul (O-FH) interface configuration mismatch at {site}. eAxC ID mapping error prevented O-RU from accepting DL beamforming weights.",
            "Corrected eAxC ID mapping table in O-DU configuration. Re-synchronized O-FH M-Plane (NETCONF) configuration with O-RU. Beamforming weights applied successfully.",
        ),
        (
            "Cloud-RAN {vendor} vCU control plane pod CPU throttling at {site}. Kubernetes CPU limit too restrictive causing PDCP/RRC processing delays exceeding 50 ms.",
            "Increased vCU CPU request from 4 to 8 cores and limit from 6 to 12 cores. Applied CPU pinning with isolcpus kernel parameter. Control plane latency normalized to <5 ms.",
        ),
        (
            "{vendor} Cloud-RAN SMO (Service Management and Orchestration) lost connectivity to {count} O-RUs at {site}. M-Plane NETCONF session timeout due to management network congestion.",
            "Isolated management traffic on dedicated VLAN with bandwidth guarantee. Increased NETCONF session keepalive interval. SMO connectivity restored to all O-RUs.",
        ),
        (
            "Cloud-RAN {vendor} vDU persistent volume at {site} filled to 95% capacity. Log files consumed disk space causing pod restart loop (CrashLoopBackOff).",
            "Cleared old log files and expanded persistent volume from 50 GB to 200 GB. Implemented log rotation with 7-day retention. Container restarted successfully. Disk usage at 12%.",
        ),
        (
            "{vendor} Cloud-RAN xApp (near-RT RIC) at {site} pushed invalid RRM policy. Incorrect A1 policy caused mass handover storm affecting {count} UEs.",
            "Rolled back xApp to previous version via CI/CD pipeline. Cleared invalid A1 policies from near-RT RIC. Re-applied validated RRM configuration. Handover storm subsided.",
        ),
        (
            "Cloud-RAN {vendor} O-CU-UP user plane pod at {site} experienced GTP-U encapsulation errors. Incorrect TEID mapping caused data plane packet drops for 20% of active PDU sessions.",
            "Restarted O-CU-UP pod with fresh session state. Applied configuration fix for TEID allocation pool size. Verified GTP-U tunnel integrity for all active PDU sessions.",
        ),
        (
            "{vendor} Cloud-RAN Kubernetes cluster at {site} node failure (etcd quorum loss). Control plane unavailable for 8 minutes preventing pod scheduling and healing.",
            "Restored etcd quorum by replacing failed etcd member node. Re-joined worker nodes to cluster. Verified pod scheduling resumed. Implemented etcd backup job with 1-hour intervals.",
        ),
        (
            "Cloud-RAN {vendor} O-RAN E2 interface at {site} dropped connection between near-RT RIC and {count} E2 nodes. gRPC stream timeout caused control loop disruption.",
            "Restarted E2 manager service in near-RT RIC. Re-established E2 subscriptions for all affected E2 nodes. Increased gRPC keepalive timeout from 10s to 30s.",
        ),
        (
            "{vendor} Cloud-RAN service mesh (Istio) certificate rotation failure at {site}. mTLS certificates expired, causing all inter-microservice communication to fail simultaneously.",
            "Manually triggered Istio certificate rotation using 'istioctl experimental cert-manager'. Updated certificate validity period to 90 days. Automatic rotation re-enabled with 30-day renewal.",
        ),
        (
            "Cloud-RAN {vendor} O-DU real-time thread scheduling failure at {site}. Kernel preemption caused missed TTI (Transmission Time Interval) deadlines, degrading radio performance.",
            "Applied PREEMPT_RT kernel patch to bare-metal host. Configured SCHED_FIFO priority for real-time threads. Verified TTI deadline miss rate reduced from 2.3% to 0.001%.",
        ),
    ],
}


def weighted_choice(choices, weights):
    total = sum(weights)
    r = random.random() * total
    cumulative = 0
    for choice, weight in zip(choices, weights):
        cumulative += weight
        if r < cumulative:
            return choice
    return choices[-1]


def random_timestamp():
    secs = random.randint(0, TS_RANGE_SECS)
    dt = START_TS + timedelta(seconds=secs)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def outage_for_severity(severity):
    if severity == "CRITICAL":
        return random.randint(60, 480)
    elif severity == "HIGH":
        return random.randint(20, 180)
    elif severity == "MEDIUM":
        return random.randint(5, 90)
    else:  # LOW
        return random.randint(0, 30)


def make_alarm_id(date_str, seq):
    # date_str: YYYY-MM-DD
    d = date_str.replace("-", "")
    return f"ALM-{d}-{seq:04d}"


def main():
    rows = []
    seq = 1

    tech_weights = [1.0] * len(TECHNOLOGY_TYPES)  # uniform

    for _ in range(1300):
        technology = weighted_choice(TECHNOLOGY_TYPES, tech_weights)
        severity = weighted_choice(SEVERITY_CHOICES, SEVERITY_WEIGHTS)
        vendor = weighted_choice(VENDORS, VENDOR_WEIGHTS)
        region = random.choice(NETWORK_REGIONS)
        ts = random_timestamp()
        date_part = ts.split(" ")[0]
        alarm_id = make_alarm_id(date_part, seq)
        seq += 1

        outage = outage_for_severity(severity)
        service_impact = random.choice(SERVICE_IMPACTS)

        templates = TEMPLATES[technology]
        desc_tmpl, res_tmpl = random.choice(templates)

        count_val = random.randint(50, 5000)
        outage_val = outage

        incident_description = (
            desc_tmpl
            .replace("{vendor}", vendor)
            .replace("{site}", region)
            .replace("{count}", str(count_val))
            .replace("{outage}", str(outage_val))
        )
        resolution_notes = (
            res_tmpl
            .replace("{vendor}", vendor)
            .replace("{site}", region)
            .replace("{count}", str(count_val))
            .replace("{outage}", str(outage_val))
        )

        rows.append({
            "alarm_id": alarm_id,
            "incident_description": incident_description,
            "network_region": region,
            "technology_type": technology,
            "severity": severity,
            "outage_duration": outage,
            "device_vendor": vendor,
            "resolution_notes": resolution_notes,
            "timestamp": ts,
            "service_impact": service_impact,
        })

    fieldnames = [
        "alarm_id", "incident_description", "network_region",
        "technology_type", "severity", "outage_duration",
        "device_vendor", "resolution_notes", "timestamp", "service_impact",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} rows -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
